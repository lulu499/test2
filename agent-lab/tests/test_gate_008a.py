import copy
import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

from orchestration_state import new_task_state
from work_monitor_protocol import (
    CI_STATUSES,
    REVIEW_OUTCOMES,
    process_monitor_observation,
)


class Gate008ATests(unittest.TestCase):
    def test_constants_are_exact(self):
        self.assertEqual(CI_STATUSES, (None, "queued", "in_progress", "success", "failure", "cancelled"))
        self.assertEqual(REVIEW_OUTCOMES, (None, "pass", "mechanical-failure", "human-required"))

    def test_no_active_task_is_noop_and_immutable(self):
        state = new_task_state("x")
        state["active_task"] = None
        state["pending_action"] = None
        original = copy.deepcopy(state)
        result = process_monitor_observation(state)
        self.assertEqual(result["decision"], "noop")
        self.assertEqual(state, original)
        self.assertEqual(result["state"], original)
        self.assertIsNot(result["state"], state)

    def test_human_required_is_terminal(self):
        state = new_task_state("x")
        state["pending_action"] = "human"
        state["human_required"] = True
        result = process_monitor_observation(state, candidate_commit="abc")
        self.assertEqual(result["decision"], "human-required")
        self.assertEqual(result["state"], state)

    def test_await_agent_ignores_missing_and_records_new_commit_once(self):
        state = new_task_state("x")
        self.assertEqual(process_monitor_observation(state)["decision"], "noop")
        first = process_monitor_observation(state, candidate_commit="abc")
        self.assertEqual(first["decision"], "commit-recorded")
        self.assertEqual(first["state"]["last_processed_commit"], "abc")
        self.assertEqual(first["state"]["pending_action"], "await-ci")
        replay = process_monitor_observation(first["state"], candidate_commit="abc")
        self.assertIn(replay["decision"], ("ci-pending", "noop"))
        self.assertNotEqual(replay["decision"], "commit-recorded")

    def test_await_ci_pending_and_terminal_paths(self):
        state = process_monitor_observation(new_task_state("x"), candidate_commit="abc")["state"]
        for pending in (None, "queued", "in_progress"):
            result = process_monitor_observation(state, ci_status=pending)
            self.assertEqual(result["decision"], "ci-pending")
            self.assertEqual(result["state"], state)
        for terminal in ("success", "failure", "cancelled"):
            result = process_monitor_observation(state, ci_status=terminal)
            self.assertEqual(result["decision"], "ready-for-review")
            self.assertEqual(result["state"]["pending_action"], "review")

    def test_await_ci_without_commit_is_inconsistent(self):
        state = new_task_state("x")
        state["pending_action"] = "await-ci"
        with self.assertRaises(ValueError):
            process_monitor_observation(state, ci_status="success")

    def test_review_pass_completes_task(self):
        state = process_monitor_observation(new_task_state("x"), candidate_commit="abc")["state"]
        state = process_monitor_observation(state, ci_status="success")["state"]
        result = process_monitor_observation(state, review_outcome="pass")
        self.assertEqual(result["decision"], "task-passed")
        self.assertIsNone(result["state"]["active_task"])
        self.assertEqual(result["state"]["last_passed_task"], "x")
        self.assertEqual(result["state"]["last_processed_commit"], "abc")

    def test_review_human_required_escalates(self):
        state = process_monitor_observation(new_task_state("x"), candidate_commit="abc")["state"]
        state = process_monitor_observation(state, ci_status="failure")["state"]
        result = process_monitor_observation(state, review_outcome="human-required")
        self.assertEqual(result["decision"], "human-required")
        self.assertTrue(result["state"]["human_required"])
        self.assertEqual(result["state"]["pending_action"], "human")

    def test_mechanical_failure_dispatches_correction_with_attempt_key(self):
        state = new_task_state("x", max_auto_retries=2)
        state["extra"] = {"preserve": True}
        state = process_monitor_observation(state, candidate_commit="abc")["state"]
        state = process_monitor_observation(state, ci_status="failure")["state"]
        original = copy.deepcopy(state)
        result = process_monitor_observation(state, review_outcome="mechanical-failure")
        self.assertEqual(result["decision"], "dispatch-correction")
        self.assertEqual(result["attempt_key"], "x:attempt-2")
        self.assertEqual(result["state"]["retry_count"], 1)
        self.assertEqual(result["state"]["active_attempt"], 2)
        self.assertEqual(result["state"]["pending_action"], "await-agent")
        self.assertIsNone(result["state"]["last_processed_commit"])
        self.assertEqual(result["state"]["extra"], {"preserve": True})
        self.assertEqual(state, original)

    def test_retry_exhaustion_escalates_without_incrementing_again(self):
        state = new_task_state("x", max_auto_retries=0)
        state = process_monitor_observation(state, candidate_commit="abc")["state"]
        state = process_monitor_observation(state, ci_status="failure")["state"]
        result = process_monitor_observation(state, review_outcome="mechanical-failure")
        self.assertEqual(result["decision"], "human-required")
        self.assertTrue(result["state"]["human_required"])
        self.assertEqual(result["state"]["pending_action"], "human")
        self.assertEqual(result["state"]["active_attempt"], 1)
        self.assertEqual(result["state"]["retry_count"], 0)

    def test_invalid_observations_raise(self):
        state = new_task_state("x")
        with self.assertRaises(ValueError):
            process_monitor_observation(state, ci_status="wat")
        with self.assertRaises(ValueError):
            process_monitor_observation(state, review_outcome="wat")


if __name__ == "__main__":
    unittest.main()
