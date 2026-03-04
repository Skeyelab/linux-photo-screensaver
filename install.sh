#!/usr/bin/env bash
# install.sh – install Linux Photo Screensaver for the current user
#
# After installation the screensaver appears in:
#   • xscreensaver-settings  (all Linux Mint editions when XScreenSaver is used)
#   • MATE Screensaver preferences
#   • Xfce Screensaver preferences
#
# On Cinnamon (the default Linux Mint edition) the native cinnamon-screensaver
# does not support third-party plugins.  This installer offers to replace it
# with XScreenSaver, which does – and which then shows Photo Screensaver in its
# settings dialog just like any other screensaver.
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
        sudo apt-get install -y \
            python3-pip python3-tk python3-pil python3-pil.imagetk \
            xprintidle xscreensaver
    elif command -v dnf &>/dev/null; then
        echo "Installing system packages via dnf…"
        sudo dnf install -y \
            python3-pip python3-tkinter python3-pillow \
            xprintidle xscreensaver
    elif command -v pacman &>/dev/null; then
        echo "Installing system packages via pacman…"
        sudo pacman -S --noconfirm \
            python-pip tk python-pillow \
            xprintidle xscreensaver
    else
        echo "WARNING: Unknown package manager."
        echo "Please install python3-pip, python3-tk, python3-pil, xprintidle, and xscreensaver manually."
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

# ── Wrapper scripts in ~/.local/bin ───────────────────────────────────────
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

# ── Locate the XScreenSaver hack directory ────────────────────────────────
find_hack_dir() {
    for d in \
        /usr/libexec/xscreensaver \
        /usr/lib/xscreensaver \
        "/usr/lib/$(uname -m)-linux-gnu/xscreensaver"
    do
        [ -d "$d" ] && echo "$d" && return
    done
    echo "/usr/lib/xscreensaver"   # fallback – will be created below
}

HACK_DIR="$(find_hack_dir)"
XSCREENSAVER_CONFIG_DIR="/usr/share/xscreensaver/config"
SCREENSAVER_DESKTOP_DIR="/usr/share/applications/screensavers"

# ── Install as an XScreenSaver hack (system-wide) ─────────────────────────
echo "Installing XScreenSaver hack to $HACK_DIR…"
sudo mkdir -p "$HACK_DIR"

# The hack is a thin shell wrapper so the Python install path is embedded once
sudo tee "$HACK_DIR/photo-screensaver" > /dev/null <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/screensaver.py" "\$@"
EOF
sudo chmod +x "$HACK_DIR/photo-screensaver"

# ── Install XScreenSaver XML config ───────────────────────────────────────
echo "Installing XScreenSaver config to $XSCREENSAVER_CONFIG_DIR…"
sudo mkdir -p "$XSCREENSAVER_CONFIG_DIR"
sudo cp "$SCRIPT_DIR/photo-screensaver.xml" "$XSCREENSAVER_CONFIG_DIR/"

# ── Install MATE / Xfce screensaver .desktop entry ────────────────────────
echo "Installing screensaver .desktop entry to $SCREENSAVER_DESKTOP_DIR…"
sudo mkdir -p "$SCREENSAVER_DESKTOP_DIR"
sudo tee "$SCREENSAVER_DESKTOP_DIR/photo-screensaver.desktop" > /dev/null <<EOF
[Desktop Entry]
Name=Photo Screensaver
Comment=Displays a slideshow of photos including all subfolders
TryExec=$HACK_DIR/photo-screensaver
Exec=$HACK_DIR/photo-screensaver
Type=Application
EOF

# ── Autostart entry – standalone daemon (non-XScreenSaver mode) ───────────
# (Skipped when XScreenSaver is chosen as the idle handler – see below)
install_daemon_autostart() {
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
}

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

# ── Cinnamon: offer to replace cinnamon-screensaver with XScreenSaver ─────
CINNAMON_DETECTED=false
if [ "${XDG_CURRENT_DESKTOP:-}" = "X-Cinnamon" ] || \
   [ "${DESKTOP_SESSION:-}" = "cinnamon" ] || \
   pgrep -x cinnamon &>/dev/null; then
    CINNAMON_DETECTED=true
fi

if $CINNAMON_DETECTED; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  Cinnamon detected                                           ║"
    echo "║                                                              ║"
    echo "║  Cinnamon's built-in screensaver does not support           ║"
    echo "║  third-party screensaver plugins.                           ║"
    echo "║                                                              ║"
    echo "║  To make Photo Screensaver appear in System Settings →      ║"
    echo "║  Screensaver, XScreenSaver can replace cinnamon-screensaver.║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    read -r -p "Replace cinnamon-screensaver with XScreenSaver? [y/N] " REPLY
    if [[ "${REPLY:-n}" =~ ^[Yy]$ ]]; then
        # Disable cinnamon-screensaver at the system autostart level
        CINNAMON_SS=/etc/xdg/autostart/cinnamon-screensaver.desktop
        if [ -f "$CINNAMON_SS" ]; then
            sudo cp "$CINNAMON_SS" "${CINNAMON_SS}.disabled"
            if sudo grep -q '^Hidden=' "$CINNAMON_SS" 2>/dev/null; then
                sudo sed -i 's/^Hidden=.*/Hidden=true/' "$CINNAMON_SS"
            else
                echo "Hidden=true" | sudo tee -a "$CINNAMON_SS" > /dev/null
            fi
            echo "cinnamon-screensaver disabled."
        fi

        # Start XScreenSaver at login (user autostart)
        mkdir -p "$AUTOSTART_DIR"
        cat > "$AUTOSTART_DIR/xscreensaver.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=XScreenSaver
Comment=Screensaver manager
Exec=xscreensaver -nosplash
X-Cinnamon-Autostart-enabled=true
NoDisplay=false
Hidden=false
EOF
        echo "XScreenSaver autostart entry created."
        echo ""
        echo "→ Log out and back in, then open:"
        echo "    xscreensaver-settings"
        echo "  to choose Photo Screensaver from the list."
    else
        echo ""
        echo "Keeping cinnamon-screensaver.  Installing standalone daemon instead."
        install_daemon_autostart
        echo "The daemon will start automatically on your next login."
    fi
else
    # Non-Cinnamon desktop: install the daemon autostart as a fallback
    install_daemon_autostart
fi

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Commands:"
echo "  photo-screensaver --daemon   # Start background idle monitor (standalone)"
echo "  photo-screensaver --run      # Test screensaver immediately"
echo "  photo-screensaver --config   # Open settings GUI"
echo "  photo-screensaver-config     # Open settings GUI (shortcut)"
echo ""
echo "Screensaver manager integration:"
echo "  • Run 'xscreensaver-settings' and select Photo Screensaver"
echo "  • The screensaver also appears in MATE and Xfce screensaver preferences"

