import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

import app


class Gate004BTests(unittest.TestCase):
    def test_current_readiness_is_explicit(self):
        self.assertEqual(app._CURRENT_READINESS, "ready")

    def test_current_readiness_is_in_contract(self):
        self.assertIn(app._CURRENT_READINESS, app.READINESS_STATES)

    def test_status_uses_current_readiness(self):
        self.assertEqual(app.status(), app._CURRENT_READINESS)

    def test_contract_and_public_behavior_unchanged(self):
        self.assertEqual(app.READINESS_STATES, ("ready", "degraded", "maintenance"))
        self.assertEqual(app.status(), "ready")
        self.assertEqual(app.build_info(), {"version": app.APP_VERSION, "status": "ready"})
        self.assertEqual(app.greeting(" Ada "), "Hello, Ada!")
        self.assertEqual(app.version(), app.APP_VERSION)


if __name__ == "__main__":
    unittest.main()
