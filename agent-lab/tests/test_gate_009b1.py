import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

import gate009b1_fixture


class Gate009B1Tests(unittest.TestCase):
    def test_probe_a_exact(self):
        self.assertEqual(gate009b1_fixture.MONITOR_LIFECYCLE_PROBE_A, "GATE009B_SUCCESSOR_A")
        self.assertEqual(gate009b1_fixture.probe_a(), "GATE009B_SUCCESSOR_A")


if __name__ == "__main__":
    unittest.main()
