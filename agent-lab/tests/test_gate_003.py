import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

from app import APP_VERSION, build_info, greeting, status, version


class Gate003Tests(unittest.TestCase):
    def test_status_is_string_contract(self):
        self.assertIsInstance(status(), str)

    def test_current_status_is_ready(self):
        self.assertEqual(status(), "ready")

    def test_status_value_is_from_public_contract(self):
        self.assertIn(status(), {"ready", "degraded", "maintenance"})

    def test_build_info_status_remains_unchanged(self):
        self.assertEqual(build_info(), {"version": APP_VERSION, "status": "ready"})

    def test_existing_behavior_remains_unchanged(self):
        self.assertEqual(greeting(" Ada "), "Hello, Ada!")
        self.assertEqual(version(), APP_VERSION)


if __name__ == "__main__":
    unittest.main()
