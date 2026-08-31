import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

from app import APP_VERSION, READINESS_STATES, build_info, greeting, status, version


class Gate004ATests(unittest.TestCase):
    def test_readiness_states_exact_contract(self):
        self.assertEqual(READINESS_STATES, ("ready", "degraded", "maintenance"))

    def test_readiness_states_is_immutable_tuple(self):
        self.assertIsInstance(READINESS_STATES, tuple)

    def test_current_status_is_in_contract(self):
        self.assertEqual(status(), "ready")
        self.assertIn(status(), READINESS_STATES)

    def test_existing_behavior_unchanged(self):
        self.assertEqual(build_info(), {"version": APP_VERSION, "status": "ready"})
        self.assertEqual(greeting(" Ada "), "Hello, Ada!")
        self.assertEqual(version(), APP_VERSION)


if __name__ == "__main__":
    unittest.main()
