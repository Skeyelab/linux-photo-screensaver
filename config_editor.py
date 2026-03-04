#!/usr/bin/env python3
"""Configuration editor GUI for Linux Photo Screensaver."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from config import load_config, save_config
from screensaver import find_images


class ConfigEditorApp:
    """Tkinter-based settings editor for the screensaver."""

    def __init__(self):
        self._config = load_config()
        self._root = tk.Tk()
        self._root.title("Photo Screensaver – Settings")
        self._root.resizable(False, False)
        self._build_ui()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self):
        """Enter the Tk main-loop."""
        self._root.mainloop()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # ---- Photo folder row ----------------------------------------
        tk.Label(self._root, text="Photo Folder:").grid(
            row=0, column=0, sticky="w", **pad
        )

        folder_frame = tk.Frame(self._root)
        folder_frame.grid(row=0, column=1, columnspan=2, sticky="ew", **pad)

        self._folder_var = tk.StringVar(value=self._config.get("photo_folder", ""))
        self._folder_var.trace_add("write", lambda *_: self._schedule_scan())
        tk.Entry(folder_frame, textvariable=self._folder_var, width=42).pack(
            side="left", fill="x", expand=True
        )
        tk.Button(folder_frame, text="Browse…", command=self._browse_folder).pack(
            side="right", padx=(5, 0)
        )

        # ---- Image count (subfolder scan result) ---------------------
        self._scan_var = tk.StringVar(value="")
        tk.Label(self._root, textvariable=self._scan_var, fg="grey", anchor="w").grid(
            row=1, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 4)
        )
        self._scan_timer = None
        # Trigger an initial scan for the pre-loaded folder
        self._root.after(100, self._run_scan)

        # ---- Idle timeout row ----------------------------------------
        tk.Label(self._root, text="Idle Timeout (seconds):").grid(
            row=2, column=0, sticky="w", **pad
        )
        self._idle_var = tk.IntVar(value=self._config.get("idle_timeout", 300))
        tk.Spinbox(
            self._root,
            from_=30,
            to=3600,
            increment=30,
            textvariable=self._idle_var,
            width=8,
        ).grid(row=2, column=1, sticky="w", **pad)
        tk.Label(self._root, text="(30 – 3600)", fg="grey").grid(
            row=2, column=2, sticky="w"
        )

        # ---- Photo interval row --------------------------------------
        tk.Label(self._root, text="Photo Interval (seconds):").grid(
            row=3, column=0, sticky="w", **pad
        )
        self._interval_var = tk.IntVar(value=self._config.get("photo_interval", 10))
        tk.Spinbox(
            self._root,
            from_=1,
            to=300,
            increment=1,
            textvariable=self._interval_var,
            width=8,
        ).grid(row=3, column=1, sticky="w", **pad)
        tk.Label(self._root, text="(1 – 300)", fg="grey").grid(
            row=3, column=2, sticky="w"
        )

        # ---- Button row ----------------------------------------------
        btn_frame = tk.Frame(self._root)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=(4, 12))

        tk.Button(btn_frame, text="Save", width=10, command=self._save).pack(
            side="left", padx=5
        )
        tk.Button(
            btn_frame, text="Cancel", width=10, command=self._root.destroy
        ).pack(side="left", padx=5)
        tk.Button(
            btn_frame,
            text="Test Screensaver",
            width=16,
            command=self._test_screensaver,
        ).pack(side="left", padx=5)

    # ------------------------------------------------------------------
    # Folder scan (runs in a background thread to keep the UI responsive)
    # ------------------------------------------------------------------

    def _schedule_scan(self):
        """Debounce rapid keystroke changes – scan 400 ms after the last edit."""
        if self._scan_timer is not None:
            self._root.after_cancel(self._scan_timer)
        self._scan_var.set("Scanning…")
        self._scan_timer = self._root.after(400, self._run_scan)

    def _run_scan(self):
        """Launch a background thread to count images (including subfolders)."""
        folder = self._folder_var.get().strip()
        self._scan_var.set("Scanning…")

        def _scan():
            if not folder or not Path(folder).is_dir():
                result = "⚠  Folder not found"
            else:
                images = find_images(folder)
                # Count how many unique subdirectory levels contain images
                subdirs = {
                    str(Path(p).parent)
                    for p in images
                    if str(Path(p).parent) != folder
                }
                if not images:
                    result = "No images found in this folder or its subfolders"
                elif subdirs:
                    result = (
                        f"✔  {len(images)} images found"
                        f" (including {len(subdirs)} subfolder"
                        f"{'s' if len(subdirs) != 1 else ''})"
                    )
                else:
                    result = f"✔  {len(images)} images found"
            # Update the label from the main thread
            self._root.after(0, lambda: self._scan_var.set(result))

        threading.Thread(target=_scan, daemon=True).start()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _browse_folder(self):
        folder = filedialog.askdirectory(
            title="Select Photo Folder",
            initialdir=self._folder_var.get() or str(Path.home()),
        )
        if folder:
            self._folder_var.set(folder)

    def _save(self):
        folder = self._folder_var.get().strip()
        if not folder or not Path(folder).is_dir():
            messagebox.showerror(
                "Invalid Folder",
                "Please select an existing photo folder.",
            )
            return

        self._config["photo_folder"] = folder
        self._config["idle_timeout"] = int(self._idle_var.get())
        self._config["photo_interval"] = int(self._interval_var.get())
        save_config(self._config)
        messagebox.showinfo("Saved", "Settings saved successfully.")

    def _test_screensaver(self):
        """Save current settings and immediately run the screensaver."""
        self._save()
        self._root.destroy()

        from screensaver import PhotoScreensaverWindow
        from config import load_config as _load

        PhotoScreensaverWindow(_load()).show()


if __name__ == "__main__":
    ConfigEditorApp().run()
