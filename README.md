# linux-photo-screensaver

A Linux photo screensaver that works just like the built-in slideshow screensaver
in Linux Mint — **but also scans all subfolders** so your entire photo library is
included automatically.

It integrates with the system screensaver manager so it **appears in the
screensaver selector** alongside every other screensaver — no manual terminal
commands needed after installation.

## Features

- Activates when the computer has been idle for a configurable amount of time
- Cycles through **random photos** at a user-configurable interval
- **Recursively searches** the selected folder and every subfolder beneath it
- Settings editor shows exactly how many images were found across all subfolders
- Supports JPG, JPEG, PNG, GIF, BMP, WebP, and TIFF formats
- Exits immediately when the mouse is moved or a key is pressed
- GUI settings editor with folder browser and live image count
- **Appears in the screensaver list** of XScreenSaver, MATE Screensaver, and Xfce Screensaver
- Supports the XScreenSaver embedded-window protocol so live preview works in settings dialogs

## Why this app?

Linux Mint's built-in photo screensaver (and most XScreenSaver slideshow hacks)
only look at a **single flat folder** — photos inside nested subfolders are ignored.
This app solves that by using a recursive scan, so a folder structure like:

```
~/Pictures/
    2023/
        January/   ← included
        February/  ← included
    2024/
        Holidays/  ← included
```

…works exactly as expected.

## Screensaver manager support

| Desktop | Screensaver manager | Appears in list? | Notes |
|---|---|---|---|
| Cinnamon (Linux Mint default) | cinnamon-screensaver | ✗ natively | Installer offers to replace with XScreenSaver ✔ |
| Cinnamon + XScreenSaver | xscreensaver | ✔ | Select in `xscreensaver-settings` |
| MATE | mate-screensaver | ✔ | Appears automatically after install |
| Xfce | xfce4-screensaver | ✔ | Appears automatically after install |

### How it works with XScreenSaver

XScreenSaver calls the screensaver as a subprocess and passes the window to draw
into via the `XSCREENSAVER_WINDOW` environment variable or the `-window-id`
command-line argument.  This app handles both, enabling the live preview in
`xscreensaver-settings`.

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.8+ | Standard on most Linux distros |
| `python3-tk` | Usually available via your package manager |
| `python3-pil` / `python3-pil.imagetk` | Pillow — image loading |
| `xprintidle` | Idle-time detection (standalone daemon mode) |
| `xscreensaver` | Needed to appear in Cinnamon's screensaver list |

## Installation

```bash
chmod +x install.sh
./install.sh
```

The installer will:
1. Install system packages (`python3-tk`, `python3-pil`, `xprintidle`, `xscreensaver`)
2. Copy the app to `~/.local/share/linux-photo-screensaver/`
3. Create `photo-screensaver` and `photo-screensaver-config` commands in `~/.local/bin/`
4. Install the XScreenSaver hack to `/usr/lib/xscreensaver/photo-screensaver`
5. Install the XScreenSaver XML config to `/usr/share/xscreensaver/config/`
6. Install a screensaver `.desktop` entry for MATE and Xfce
7. **On Cinnamon**: offer to replace `cinnamon-screensaver` with XScreenSaver and add it to autostart

### Manual dependency install (Debian / Ubuntu / Linux Mint)

```bash
sudo apt install python3-tk python3-pil python3-pil.imagetk xprintidle xscreensaver
pip3 install --user Pillow
```

## Usage

### Screensaver manager (recommended)

After running `install.sh`, open your screensaver settings:

- **Cinnamon + XScreenSaver**: run `xscreensaver-settings`, find *Photo Screensaver* in the list
- **MATE**: *System Settings → Screensaver* → select *Photo Screensaver*
- **Xfce**: *Settings → Screensaver* → select *Photo Screensaver*

Configure the photo folder first:

```bash
photo-screensaver --config
```

### Standalone daemon (alternative, no XScreenSaver needed)

```bash
photo-screensaver --daemon
# or directly:
python3 screensaver.py --daemon
```

The daemon polls the system idle time every second. When the computer has been
idle for longer than the configured *Idle Timeout*, it launches the screensaver
fullscreen. The screensaver closes the moment you move the mouse or press any key.

### Open the settings editor

```bash
photo-screensaver --config
# or:
python3 config_editor.py
```

The settings editor lets you:
- **Browse** to any folder — all subfolders are included automatically
- See a live count of images found (e.g. *"✔ 1,247 images found (including 34 subfolders)"*)
- Set the **Idle Timeout** (30 – 3,600 seconds)
- Set the **Photo Interval** (1 – 300 seconds)
- Click **Test Screensaver** to preview immediately

### Test the screensaver immediately

```bash
photo-screensaver --run
# or:
python3 screensaver.py --run
```

## Configuration

Settings are saved to `~/.config/linux-photo-screensaver/config.json`.

| Key | Default | Description |
|---|---|---|
| `photo_folder` | `~/Pictures` | Root folder — all subfolders are included |
| `idle_timeout` | `300` | Seconds of inactivity before the screensaver starts |
| `photo_interval` | `10` | Seconds each photo is displayed |

Example `config.json`:

```json
{
  "photo_folder": "/home/alice/Pictures",
  "idle_timeout": 300,
  "photo_interval": 10
}
```

## Supported image formats

`.jpg` · `.jpeg` · `.png` · `.gif` · `.bmp` · `.webp` · `.tiff` · `.tif`

## Running tests

```bash
python3 -m pytest tests/ -v
```

