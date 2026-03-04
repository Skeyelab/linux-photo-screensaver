"""Configuration management for Linux Photo Screensaver."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "photo_folder": str(Path.home() / "Pictures"),
    "idle_timeout": 300,   # seconds of idle time before screensaver activates
    "photo_interval": 10,  # seconds between photo changes
}

CONFIG_DIR = Path.home() / ".config" / "linux-photo-screensaver"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config():
    """Load configuration from file, merging with defaults for missing keys."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not load config file, using defaults: %s", e)
    return config


def save_config(config):
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
