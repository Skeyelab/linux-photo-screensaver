#!/usr/bin/env python3
"""Linux Photo Screensaver

Displays photos from a configurable folder when the system is idle.

Usage:
  python3 screensaver.py --daemon        # Monitor idle time and launch screensaver
  python3 screensaver.py --run           # Run screensaver immediately (for testing)
  python3 screensaver.py --config        # Open configuration editor
  python3 screensaver.py --window-id ID  # Embed into X window ID (XScreenSaver protocol)

XScreenSaver / MATE / Xfce screensaver managers call this script directly and
either set the XSCREENSAVER_WINDOW environment variable or pass -window-id WINDOWID
on the command line.  The screensaver detects both and embeds itself into the
provided window, which enables the live preview in screensaver settings dialogs.
"""

import argparse
import logging
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Supported image file extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}


def find_images(folder):
    """Recursively find all image files in *folder* and its subfolders.

    Returns a list of absolute path strings sorted for reproducibility.
    """
    images = []
    try:
        for root, _dirs, files in os.walk(folder):
            for filename in files:
                if Path(filename).suffix.lower() in IMAGE_EXTENSIONS:
                    images.append(os.path.join(root, filename))
    except OSError as e:
        logger.error("Error scanning folder %s: %s", folder, e)
    return sorted(images)


def get_idle_time_ms():
    """Return the number of milliseconds the system has been idle.

    Uses *xprintidle* which queries the X server for the idle time.
    Returns 0 if xprintidle is unavailable or the call fails.
    """
    try:
        result = subprocess.run(
            ["xprintidle"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
        logger.debug("Could not get idle time: %s", e)
    return 0


class PhotoScreensaverWindow:
    """Fullscreen photo display window.

    Requires a running X display.  Call :meth:`show` to enter the
    blocking Tk main-loop; the window closes on any keyboard or mouse event.
    """

    def __init__(self, config):
        self.config = config
        self._images = []
        self._index = 0
        self._root = None
        self._label = None
        self._photo = None   # keep reference to prevent GC
        self._running = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def show(self, window_id=None):
        """Display the screensaver.  Blocks until the user dismisses it.

        Parameters
        ----------
        window_id : int or None
            When given, embed the slideshow into this X window (XScreenSaver
            protocol).  When ``None``, open a normal fullscreen window.
        """
        import tkinter as tk
        from PIL import Image, ImageTk  # noqa: F401 – imported for side effects

        self._load_images()
        if not self._images:
            logger.error(
                "No images found in '%s'. "
                "Use --config to set a photo folder.",
                self.config.get("photo_folder"),
            )
            return

        self._running = True
        self._embedded = window_id is not None

        if self._embedded:
            # Embed into the window provided by the screensaver manager
            self._root = tk.Tk(use=window_id)
        else:
            self._root = tk.Tk()
            self._root.attributes("-fullscreen", True)
            self._root.attributes("-topmost", True)
            self._root.configure(cursor="none")   # hide the mouse cursor
            # Close on any keyboard or mouse event
            for event in ("<Any-KeyPress>", "<Motion>", "<Button>"):
                self._root.bind(event, self._on_user_input)

        self._root.title("Photo Screensaver")
        self._root.configure(bg="black")

        self._label = tk.Label(self._root, bg="black")
        self._label.place(relx=0.5, rely=0.5, anchor="center")

        # Display the first photo after a short delay to let Tk settle
        self._root.after(100, self._show_next_photo)
        self._root.mainloop()
        self._running = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_images(self):
        folder = self.config.get("photo_folder", str(Path.home() / "Pictures"))
        self._images = find_images(folder)
        if self._images:
            random.shuffle(self._images)
            logger.info("Found %d images in %s", len(self._images), folder)
        else:
            logger.warning("No images found in %s", folder)

    def _show_next_photo(self):
        """Load and display the next image, then schedule the following one."""
        from PIL import Image, ImageTk

        if not self._running or self._root is None:
            return

        image_path = self._images[self._index % len(self._images)]
        self._index += 1

        try:
            img = Image.open(image_path)
            if getattr(self, "_embedded", False):
                # Use the actual size of the embedded preview window
                self._root.update_idletasks()
                screen_w = self._root.winfo_width() or 640
                screen_h = self._root.winfo_height() or 480
            else:
                screen_w = self._root.winfo_screenwidth()
                screen_h = self._root.winfo_screenheight()

            # Scale to fill the screen while preserving the aspect ratio
            img_ratio = img.width / img.height
            screen_ratio = screen_w / screen_h
            if img_ratio > screen_ratio:
                new_w = screen_w
                new_h = int(screen_w / img_ratio)
            else:
                new_h = screen_h
                new_w = int(screen_h * img_ratio)

            img = img.resize((new_w, new_h), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            self._label.configure(image=self._photo)
        except Exception as e:
            logger.error("Failed to load image %s: %s", image_path, e)
            # Skip broken image – schedule immediately
            self._root.after(0, self._show_next_photo)
            return

        interval_ms = int(self.config.get("photo_interval", 10) * 1000)
        self._root.after(interval_ms, self._show_next_photo)

    def _on_user_input(self, _event):
        """Handle any user input by closing the screensaver."""
        self._running = False
        if self._root is not None:
            self._root.destroy()
            self._root = None


class ScreensaverDaemon:
    """Background daemon that monitors idle time and launches the screensaver.

    When the system has been idle for longer than ``idle_timeout`` seconds,
    ``screensaver.py --run`` is launched as a child process.  The daemon waits
    for that child to exit (which happens when the user moves the mouse or
    presses a key) before resuming idle monitoring.
    """

    def __init__(self):
        self.config = load_config()
        self._running = True

    def run(self):
        """Enter the main monitoring loop.  Blocks until :meth:`stop` is called."""
        logger.info("Screensaver daemon started")
        logger.info("  Photo folder   : %s", self.config.get("photo_folder"))
        logger.info("  Idle timeout   : %ds", self.config.get("idle_timeout"))
        logger.info("  Photo interval : %ds", self.config.get("photo_interval"))

        while self._running:
            idle_ms = get_idle_time_ms()
            threshold_ms = self.config.get("idle_timeout", 300) * 1000

            if idle_ms >= threshold_ms:
                logger.info(
                    "System idle for %.1fs – launching screensaver",
                    idle_ms / 1000,
                )
                self._launch_screensaver()
                # Reload config after the screensaver exits so changes take effect
                self.config = load_config()
            else:
                time.sleep(1)

    def stop(self):
        """Stop the daemon loop."""
        self._running = False

    def _launch_screensaver(self):
        """Run the screensaver in a child process and wait for it to finish."""
        script = os.path.abspath(__file__)
        try:
            subprocess.run([sys.executable, script, "--run"], check=False)
        except OSError as e:
            logger.error("Failed to launch screensaver: %s", e)
        # Brief pause so the idle counter doesn't immediately re-trigger
        time.sleep(2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # XScreenSaver passes -window-id with a single dash; normalise to --window-id
    # so that argparse can handle it uniformly.
    argv = ["--window-id" if a == "-window-id" else a for a in sys.argv[1:]]

    parser = argparse.ArgumentParser(
        description="Linux Photo Screensaver – cycles random photos when idle"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--daemon",
        action="store_true",
        help="Run as a background daemon that monitors idle time (default)",
    )
    group.add_argument(
        "--run",
        action="store_true",
        help="Show the screensaver immediately (useful for testing)",
    )
    group.add_argument(
        "--config",
        action="store_true",
        help="Open the configuration editor GUI",
    )
    parser.add_argument(
        "--window-id",
        dest="window_id",
        metavar="WINDOWID",
        help="X window ID for embedded mode (XScreenSaver protocol)",
    )
    args = parser.parse_args(argv)

    # Resolve window ID from --window-id arg or XSCREENSAVER_WINDOW env var.
    # XScreenSaver sets the env var (hex); our own --window-id accepts 0xHEX or decimal.
    window_id = None
    env_window = os.environ.get("XSCREENSAVER_WINDOW")
    if args.window_id:
        window_id = int(args.window_id, 0)
    elif env_window:
        window_id = int(env_window, 0)

    if args.config:
        from config_editor import ConfigEditorApp
        ConfigEditorApp().run()

    elif args.daemon:
        # Explicit daemon mode – ignore any window ID
        _run_daemon()

    elif args.run or window_id is not None:
        # Screensaver display: explicit --run, or called by a screensaver manager
        config = load_config()
        PhotoScreensaverWindow(config).show(window_id=window_id)

    else:
        # Default with no flags: daemon mode
        _run_daemon()


def _run_daemon():
    """Start the idle-monitoring daemon."""
    daemon = ScreensaverDaemon()

    def _handle_signal(sig, _frame):
        logger.info("Received signal %s – stopping daemon", sig)
        daemon.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    daemon.run()


if __name__ == "__main__":
    main()
