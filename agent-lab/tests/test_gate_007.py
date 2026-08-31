import copy
import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

import orchestration_state as os_state


class Gate007StateMachineTests(unittest.TestCase):
    def test_pending_actions_exact(self):
        self.assertEqual(
            os_state.PENDING_ACTIONS,
            ("await-agent", "await-ci", "review", "correct", "next-task", "human", None),
        )

    def test_new_task_state_defaults_and_freshness(self):
        a = os_state.new_task_state("task-x")
        b = os_state.new_task_state("task-x")
        self.assertEqual(
            a,
            {
                "active_task": "task-x",
                "active_attempt": 1,
                "last_passed_task": None,
                "human_required": False,
                "last_processed_commit": None,
                "last_processed_event": None,
                "pending_action": "await-agent",
                "retry_count": 0,
                "max_auto_retries": 2,
            },
        )
        self.assertIsNot(a, b)
        a["retry_count"] = 99
        self.assertEqual(b["retry_count"], 0)

    def test_new_task_state_validation(self):
        for task_id in ("", "   "):
            with self.assertRaises(ValueError):
                os_state.new_task_state(task_id)
        with self.assertRaises(ValueError):
            os_state.new_task_state("x", max_auto_retries=-1)

    def test_attempt_key(self):
        self.assertEqual(os_state.attempt_key("gate-007", 3), "gate-007:attempt-3")
        with self.assertRaises(ValueError):
            os_state.attempt_key("", 1)
        with self.assertRaises(ValueError):
            os_state.attempt_key("x", 0)

    def test_validate_state_accepts_valid_state(self):
        self.assertTrue(os_state.validate_state(os_state.new_task_state("task-x")))

    def test_validate_state_rejects_invalid_states(self):
        valid = os_state.new_task_state("task-x")

        for field in valid:
            broken = dict(valid)
            del broken[field]
            with self.assertRaises(ValueError, msg=field):
                os_state.validate_state(broken)

        broken = dict(valid, pending_action="bogus")
        with self.assertRaises(ValueError):
            os_state.validate_state(broken)

        for field, value in (
            ("active_attempt", 0),
            ("retry_count", -1),
            ("max_auto_retries", -1),
        ):
            broken = dict(valid, **{field: value})
            with self.assertRaises(ValueError):
                os_state.validate_state(broken)

        broken = dict(valid, retry_count=3, max_auto_retries=2)
        with self.assertRaises(ValueError):
            os_state.validate_state(broken)

        broken = dict(valid, human_required=True, pending_action="await-agent")
        with self.assertRaises(ValueError):
            os_state.validate_state(broken)

    def test_should_process_commit(self):
        state = os_state.new_task_state("task-x")
        self.assertFalse(os_state.should_process_commit(state, ""))
        self.assertTrue(os_state.should_process_commit(state, "abc"))

        processed = os_state.record_processed_commit(state, "abc")
        self.assertFalse(os_state.should_process_commit(processed, "abc"))
        self.assertTrue(os_state.should_process_commit(processed, "def"))

        inactive = os_state.complete_task(processed)
        self.assertFalse(os_state.should_process_commit(inactive, "def"))

    def test_record_processed_commit_is_immutable_and_idempotent(self):
        state = os_state.new_task_state("task-x")
        state["custom"] = {"keep": True}
        before = copy.deepcopy(state)

        once = os_state.record_processed_commit(state, "abc", pending_action="review")
        twice = os_state.record_processed_commit(once, "abc", pending_action="review")

        self.assertEqual(state, before)
        self.assertIsNot(once, state)
        self.assertEqual(once["last_processed_commit"], "abc")
        self.assertEqual(once["pending_action"], "review")
        self.assertEqual(once["custom"], {"keep": True})
        self.assertEqual(twice, once)
        self.assertIsNot(twice, once)

    def test_record_processed_commit_rejects_invalid_input(self):
        state = os_state.new_task_state("task-x")
        with self.assertRaises(ValueError):
            os_state.record_processed_commit(state, "")
        with self.assertRaises(ValueError):
            os_state.record_processed_commit(state, "abc", pending_action="bogus")

    def test_begin_auto_correction_transitions_and_retry_limit(self):
        state = os_state.new_task_state("task-x", max_auto_retries=2)
        state["last_processed_commit"] = "sha1"
        state["last_processed_event"] = "evt1"
        state["custom"] = "preserve"
        before = copy.deepcopy(state)

        correction1 = os_state.begin_auto_correction(state)
        self.assertEqual(state, before)
        self.assertEqual(correction1["active_attempt"], 2)
        self.assertEqual(correction1["retry_count"], 1)
        self.assertIsNone(correction1["last_processed_commit"])
        self.assertIsNone(correction1["last_processed_event"])
        self.assertEqual(correction1["pending_action"], "await-agent")
        self.assertFalse(correction1["human_required"])
        self.assertEqual(correction1["custom"], "preserve")

        correction2 = os_state.begin_auto_correction(correction1)
        self.assertEqual(correction2["active_attempt"], 3)
        self.assertEqual(correction2["retry_count"], 2)
        self.assertFalse(correction2["human_required"])

        exhausted = os_state.begin_auto_correction(correction2)
        self.assertEqual(exhausted["active_attempt"], 3)
        self.assertEqual(exhausted["retry_count"], 2)
        self.assertEqual(exhausted["pending_action"], "human")
        self.assertTrue(exhausted["human_required"])

    def test_complete_task_is_immutable_and_preserves_audit_identity(self):
        state = os_state.new_task_state("task-x")
        state = os_state.record_processed_commit(state, "abc", pending_action="review")
        state["last_processed_event"] = "event-1"
        state["custom"] = 7
        before = copy.deepcopy(state)

        completed = os_state.complete_task(state)

        self.assertEqual(state, before)
        self.assertEqual(completed["last_passed_task"], "task-x")
        self.assertIsNone(completed["active_task"])
        self.assertIsNone(completed["pending_action"])
        self.assertFalse(completed["human_required"])
        self.assertEqual(completed["last_processed_commit"], "abc")
        self.assertEqual(completed["last_processed_event"], "event-1")
        self.assertEqual(completed["custom"], 7)
        self.assertTrue(os_state.validate_state(completed))


if __name__ == "__main__":
    unittest.main()
