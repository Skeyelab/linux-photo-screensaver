"""Tests for config.py"""

import json
import os
import sys
import unittest
from pathlib import Path
import tempfile
import shutil

# Ensure the repo root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        # Redirect config to a temporary directory
        self._tmp = tempfile.mkdtemp()
        import config as cfg_module
        self._orig_cfg_dir = cfg_module.CONFIG_DIR
        self._orig_cfg_file = cfg_module.CONFIG_FILE
        cfg_module.CONFIG_DIR = Path(self._tmp)
        cfg_module.CONFIG_FILE = Path(self._tmp) / "config.json"
        self._cfg = cfg_module

    def tearDown(self):
        self._cfg.CONFIG_DIR = self._orig_cfg_dir
        self._cfg.CONFIG_FILE = self._orig_cfg_file
        shutil.rmtree(self._tmp)

    def test_defaults_when_no_file(self):
        config = self._cfg.load_config()
        self.assertIn("photo_folder", config)
        self.assertIn("idle_timeout", config)
        self.assertIn("photo_interval", config)
        self.assertEqual(config["idle_timeout"], 300)
        self.assertEqual(config["photo_interval"], 10)

    def test_saved_values_are_loaded(self):
        data = {"photo_folder": "/tmp/photos", "idle_timeout": 60, "photo_interval": 5}
        self._cfg.save_config(data)
        config = self._cfg.load_config()
        self.assertEqual(config["photo_folder"], "/tmp/photos")
        self.assertEqual(config["idle_timeout"], 60)
        self.assertEqual(config["photo_interval"], 5)

    def test_partial_config_merged_with_defaults(self):
        # Only override one key; others should come from defaults
        self._cfg.save_config({"photo_interval": 20})
        config = self._cfg.load_config()
        self.assertEqual(config["photo_interval"], 20)
        self.assertEqual(config["idle_timeout"], 300)   # default

    def test_corrupt_file_falls_back_to_defaults(self):
        Path(self._tmp).mkdir(parents=True, exist_ok=True)
        (Path(self._tmp) / "config.json").write_text("not valid json")
        config = self._cfg.load_config()
        self.assertEqual(config["idle_timeout"], 300)


class TestSaveConfig(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        import config as cfg_module
        self._orig_cfg_dir = cfg_module.CONFIG_DIR
        self._orig_cfg_file = cfg_module.CONFIG_FILE
        cfg_module.CONFIG_DIR = Path(self._tmp) / "subdir"
        cfg_module.CONFIG_FILE = cfg_module.CONFIG_DIR / "config.json"
        self._cfg = cfg_module

    def tearDown(self):
        self._cfg.CONFIG_DIR = self._orig_cfg_dir
        self._cfg.CONFIG_FILE = self._orig_cfg_file
        shutil.rmtree(self._tmp)

    def test_creates_directory_and_file(self):
        self._cfg.save_config({"photo_folder": "/tmp", "idle_timeout": 120, "photo_interval": 7})
        self.assertTrue(self._cfg.CONFIG_FILE.exists())
        with open(self._cfg.CONFIG_FILE) as f:
            saved = json.load(f)
        self.assertEqual(saved["idle_timeout"], 120)

    def test_roundtrip(self):
        original = {"photo_folder": "/home/user/pics", "idle_timeout": 45, "photo_interval": 3}
        self._cfg.save_config(original)
        loaded = self._cfg.load_config()
        for key, value in original.items():
            self.assertEqual(loaded[key], value)


if __name__ == "__main__":
    unittest.main()
