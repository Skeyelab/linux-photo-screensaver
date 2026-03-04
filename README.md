# linux-photo-screensaver

A Linux photo screensaver that works just like the built-in slideshow screensaver
in Linux Mint — **but also scans all subfolders** so your entire photo library is
included automatically.

## Features

- Activates when the computer has been idle for a configurable amount of time
- Cycles through **random photos** at a user-configurable interval
- **Recursively searches** the selected folder and every subfolder beneath it
- Settings editor shows exactly how many images were found across all subfolders
- Supports JPG, JPEG, PNG, GIF, BMP, WebP, and TIFF formats
- Exits immediately when the mouse is moved or a key is pressed
- GUI settings editor with folder browser and live image count
- Autostart entry so the daemon launches automatically at login

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

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.8+ | Standard on most Linux distros |
| `python3-tk` | Usually available via your package manager |
| `python3-pil` / `python3-pil.imagetk` | Pillow — image loading |
| `xprintidle` | Idle-time detection (X11) |

## Installation

```bash
chmod +x install.sh
./install.sh
```

The installer will:
1. Install system packages (`python3-tk`, `python3-pil`, `xprintidle`) via your distro's package manager
2. Copy the app to `~/.local/share/linux-photo-screensaver/`
3. Create `photo-screensaver` and `photo-screensaver-config` commands in `~/.local/bin/`
4. Add an autostart entry so the daemon starts with every desktop session

### Manual dependency install (Debian / Ubuntu / Linux Mint)

```bash
sudo apt install python3-tk python3-pil python3-pil.imagetk xprintidle
pip3 install --user Pillow
```

## Usage

### Start the background daemon

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
- Set the **Idle Timeout** (30 – 3 600 seconds)
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
