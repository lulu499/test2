import pathlib
import sys
import unittest
from typing import Literal, get_args, get_origin, get_type_hints

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

import app


class Gate005ATests(unittest.TestCase):
    def test_readiness_state_literal_exact(self):
        self.assertIs(get_origin(app.ReadinessState), Literal)
        self.assertEqual(get_args(app.ReadinessState), ("ready", "degraded", "maintenance"))

    def test_readiness_states_runtime_contract_unchanged(self):
        self.assertEqual(app.READINESS_STATES, ("ready", "degraded", "maintenance"))
        self.assertEqual(app._CURRENT_READINESS, "ready")
        self.assertEqual(app.status(), "ready")

    def test_status_return_annotation_is_readiness_state(self):
        hints = get_type_hints(app.status)
        self.assertIs(hints["return"], app.ReadinessState)

    def test_existing_public_behavior_unchanged(self):
        self.assertEqual(app.build_info(), {"version": app.APP_VERSION, "status": "ready"})
        self.assertEqual(app.greeting(" Ada "), "Hello, Ada!")
        self.assertEqual(app.version(), app.APP_VERSION)


if __name__ == "__main__":
    unittest.main()
