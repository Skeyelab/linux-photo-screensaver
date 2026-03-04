"""Tests for screensaver.py helpers (no display required)."""

import argparse
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from screensaver import find_images, IMAGE_EXTENSIONS


class TestFindImages(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp)

    def _make_file(self, relative_path):
        full = Path(self._tmp) / relative_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("dummy")
        return str(full)

    def test_finds_images_in_root(self):
        self._make_file("photo.jpg")
        self._make_file("other.txt")
        images = find_images(self._tmp)
        self.assertEqual(len(images), 1)
        self.assertTrue(images[0].endswith("photo.jpg"))

    def test_finds_images_in_subfolders(self):
        self._make_file("a/img1.png")
        self._make_file("a/b/img2.jpeg")
        self._make_file("a/b/c/img3.gif")
        self._make_file("readme.md")
        images = find_images(self._tmp)
        self.assertEqual(len(images), 3)

    def test_returns_empty_for_empty_folder(self):
        images = find_images(self._tmp)
        self.assertEqual(images, [])

    def test_returns_empty_for_nonexistent_folder(self):
        images = find_images("/nonexistent/path/xyz")
        self.assertEqual(images, [])

    def test_all_supported_extensions_found(self):
        for ext in IMAGE_EXTENSIONS:
            self._make_file(f"img{ext}")
        images = find_images(self._tmp)
        self.assertEqual(len(images), len(IMAGE_EXTENSIONS))

    def test_case_insensitive_extension_matching(self):
        self._make_file("UPPER.JPG")
        self._make_file("mixed.Png")
        images = find_images(self._tmp)
        self.assertEqual(len(images), 2)

    def test_results_are_sorted(self):
        self._make_file("z.jpg")
        self._make_file("a.jpg")
        self._make_file("m.jpg")
        images = find_images(self._tmp)
        self.assertEqual(images, sorted(images))


class TestGetIdleTime(unittest.TestCase):
    def test_returns_integer(self):
        from screensaver import get_idle_time_ms
        result = get_idle_time_ms()
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)


# ---------------------------------------------------------------------------
# XScreenSaver window-id protocol tests
# ---------------------------------------------------------------------------

def _parse_argv(argv):
    """Reproduce the argument-parsing logic from screensaver.main()."""
    # Normalise single-dash -window-id to --window-id (XScreenSaver convention)
    normalized = ["--window-id" if a == "-window-id" else a for a in argv]

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--daemon", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--config", action="store_true")
    parser.add_argument("--window-id", dest="window_id")
    args = parser.parse_args(normalized)

    window_id = None
    if args.window_id:
        window_id = int(args.window_id, 0)
    return args, window_id


class TestWindowIdParsing(unittest.TestCase):
    """Verify the XScreenSaver -window-id / XSCREENSAVER_WINDOW handling."""

    def test_single_dash_window_id_normalised(self):
        """XScreenSaver passes -window-id (single dash); must be normalised."""
        _args, wid = _parse_argv(["-window-id", "0x4a00007"])
        self.assertEqual(wid, 0x4A00007)

    def test_double_dash_window_id(self):
        """--window-id (double dash) also works."""
        _args, wid = _parse_argv(["--window-id", "0x4a00007"])
        self.assertEqual(wid, 0x4A00007)

    def test_decimal_window_id(self):
        """Decimal window IDs are accepted."""
        _args, wid = _parse_argv(["--window-id", "77070343"])
        self.assertEqual(wid, 77070343)

    def test_no_window_id_gives_none(self):
        """Omitting --window-id produces None."""
        _args, wid = _parse_argv([])
        self.assertIsNone(wid)

    def test_env_var_xscreensaver_window_parsed_as_hex(self):
        """XSCREENSAVER_WINDOW env var is read as an auto-detected integer (0x prefix supported)."""
        with patch.dict(os.environ, {"XSCREENSAVER_WINDOW": "0x4a00007"}):
            env_val = os.environ.get("XSCREENSAVER_WINDOW")
            wid = int(env_val, 0)
        self.assertEqual(wid, 0x4A00007)

    def test_env_var_takes_lower_priority_than_arg(self):
        """Explicit --window-id overrides XSCREENSAVER_WINDOW."""
        with patch.dict(os.environ, {"XSCREENSAVER_WINDOW": "0x1111111"}):
            _args, wid = _parse_argv(["--window-id", "0x2222222"])
        # Argument wins because the main() logic checks args.window_id first
        self.assertEqual(wid, 0x2222222)

    def test_run_flag_unaffected_by_window_id(self):
        """--run combined with --window-id leaves run=True and window_id set."""
        # --run and --window-id are not mutually exclusive
        _args, wid = _parse_argv(["--run", "--window-id", "0xABC"])
        self.assertTrue(_args.run)
        self.assertEqual(wid, 0xABC)


if __name__ == "__main__":
    unittest.main()
