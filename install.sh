#!/usr/bin/env bash
# install.sh – install Linux Photo Screensaver for the current user
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/linux-photo-screensaver"
BIN_DIR="$HOME/.local/bin"
AUTOSTART_DIR="$HOME/.config/autostart"
APPLICATIONS_DIR="$HOME/.local/share/applications"

echo "=== Linux Photo Screensaver – Installer ==="
echo ""

# ── System dependencies ────────────────────────────────────────────────────
install_deps() {
    if command -v apt-get &>/dev/null; then
        echo "Installing system packages via apt-get…"
        sudo apt-get install -y python3-pip python3-tk python3-pil python3-pil.imagetk xprintidle
    elif command -v dnf &>/dev/null; then
        echo "Installing system packages via dnf…"
        sudo dnf install -y python3-pip python3-tkinter python3-pillow xprintidle
    elif command -v pacman &>/dev/null; then
        echo "Installing system packages via pacman…"
        sudo pacman -S --noconfirm python-pip tk python-pillow xprintidle
    else
        echo "WARNING: Unknown package manager."
        echo "Please install python3-pip, python3-tk, python3-pil, and xprintidle manually."
    fi
}

install_deps

# ── Python dependencies ────────────────────────────────────────────────────
echo "Installing Python dependencies…"
pip3 install --user -r "$SCRIPT_DIR/requirements.txt"

# ── Copy application files ─────────────────────────────────────────────────
echo "Copying application files to $INSTALL_DIR…"
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR"/*.py "$INSTALL_DIR/"

# ── Wrapper scripts ────────────────────────────────────────────────────────
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/photo-screensaver" <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/screensaver.py" "\$@"
EOF
chmod +x "$BIN_DIR/photo-screensaver"

cat > "$BIN_DIR/photo-screensaver-config" <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/config_editor.py" "\$@"
EOF
chmod +x "$BIN_DIR/photo-screensaver-config"

# ── Autostart entry (daemon starts with desktop session) ──────────────────
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/photo-screensaver.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Photo Screensaver
Comment=Linux Photo Screensaver Daemon
Exec=$BIN_DIR/photo-screensaver --daemon
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# ── Application menu entry (settings GUI) ─────────────────────────────────
mkdir -p "$APPLICATIONS_DIR"
cat > "$APPLICATIONS_DIR/photo-screensaver-config.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Photo Screensaver Settings
Comment=Configure Linux Photo Screensaver
Exec=$BIN_DIR/photo-screensaver-config
Icon=preferences-desktop-screensaver
Terminal=false
Categories=Settings;
EOF

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Commands:"
echo "  photo-screensaver --daemon   # Start background idle monitor"
echo "  photo-screensaver --run      # Test screensaver immediately"
echo "  photo-screensaver --config   # Open settings GUI"
echo "  photo-screensaver-config     # Open settings GUI (shortcut)"
echo ""
echo "The daemon will start automatically on your next login."
echo "To start it now, run:  photo-screensaver --daemon &"
