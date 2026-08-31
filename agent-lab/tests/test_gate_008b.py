import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

import gate008b_fixture


class Gate008BTests(unittest.TestCase):
    def test_probe_constant_exact(self):
        self.assertEqual(
            gate008b_fixture.MONITOR_PROTOCOL_PROBE,
            "GATE008B_STATE_MACHINE_INTEGRATION",
        )

    def test_probe_value_returns_constant(self):
        self.assertEqual(
            gate008b_fixture.probe_value(),
            gate008b_fixture.MONITOR_PROTOCOL_PROBE,
        )


if __name__ == "__main__":
    unittest.main()
