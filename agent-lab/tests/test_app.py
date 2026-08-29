import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

from app import greeting


class GreetingTests(unittest.TestCase):
    def test_greeting_trims_name(self):
        self.assertEqual(greeting("  Lucas  "), "Hello, Lucas!")

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            greeting("   ")


if __name__ == "__main__":
    unittest.main()
