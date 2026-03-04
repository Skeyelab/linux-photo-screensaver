"""Tests for screensaver.py helpers (no display required)."""

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
