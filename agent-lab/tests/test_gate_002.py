import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

from app import APP_VERSION, build_info, greeting, version


class Gate002Tests(unittest.TestCase):
    def test_build_info_exact_shape(self):
        self.assertEqual(build_info(), {"version": APP_VERSION, "status": "ready"})

    def test_build_info_returns_fresh_dict(self):
        first = build_info()
        second = build_info()
        self.assertIsNot(first, second)

    def test_mutation_does_not_leak(self):
        first = build_info()
        first["status"] = "broken"
        first["extra"] = True
        self.assertEqual(build_info(), {"version": APP_VERSION, "status": "ready"})

    def test_existing_behavior_unchanged(self):
        self.assertEqual(greeting(" Ada "), "Hello, Ada!")
        self.assertEqual(version(), APP_VERSION)


if __name__ == "__main__":
    unittest.main()
