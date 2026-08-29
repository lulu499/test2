import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

from app import APP_VERSION, greeting, version


class GreetingTests(unittest.TestCase):
    def test_greeting_trims_name(self):
        self.assertEqual(greeting("  Lucas  "), "Hello, Lucas!")

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            greeting("   ")


class VersionTests(unittest.TestCase):
    def test_app_version_constant(self):
        self.assertEqual(APP_VERSION, "0.1.0")

    def test_version_returns_app_version(self):
        self.assertEqual(version(), APP_VERSION)
        self.assertEqual(version(), "0.1.0")


if __name__ == "__main__":
    unittest.main()
