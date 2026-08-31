import copy
import pathlib
import sys
import unittest

LAB_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))

import orchestration_state
import ledger_reconciliation


def make_state(task_id="task-a"):
    state = orchestration_state.new_task_state(task_id)
    state["marker"] = {"preserve": True}
    return state


def pass_ledger(task_id="task-a", attempt=1):
    return {
        "task_id": task_id,
        "attempt": attempt,
        "attempt_key": f"{task_id}:attempt-{attempt}",
        "status": "pass",
        "implementation_commit": "abc123",
        "processed_by_background_work": True,
    }


class Gate009ATests(unittest.TestCase):
    def test_terminal_statuses_exact(self):
        self.assertEqual(
            ledger_reconciliation.TERMINAL_LEDGER_STATUSES,
            ("pass", "human-required"),
        )

    def test_ledger_event_id(self):
        ledger = pass_ledger()
        self.assertEqual(
            ledger_reconciliation.ledger_event_id(ledger),
            "task-a:attempt-1:pass",
        )

    def test_ledger_event_id_rejects_invalid_ledgers(self):
        invalid_ledgers = []
        for missing in ("task_id", "attempt", "attempt_key", "status", "processed_by_background_work"):
            ledger = pass_ledger()
            ledger.pop(missing)
            invalid_ledgers.append(ledger)

        wrong_attempt = pass_ledger()
        wrong_attempt["attempt"] = 0
        invalid_ledgers.append(wrong_attempt)

        wrong_key = pass_ledger()
        wrong_key["attempt_key"] = "wrong"
        invalid_ledgers.append(wrong_key)

        nonterminal = pass_ledger()
        nonterminal["status"] = "armed"
        invalid_ledgers.append(nonterminal)

        not_background = pass_ledger()
        not_background["processed_by_background_work"] = False
        invalid_ledgers.append(not_background)

        for ledger in invalid_ledgers:
            with self.subTest(ledger=ledger):
                with self.assertRaises(ValueError):
                    ledger_reconciliation.ledger_event_id(ledger)

    def test_pass_reconciliation_is_immutable_and_preserves_unrelated_keys(self):
        state = make_state()
        ledger = pass_ledger()
        original_state = copy.deepcopy(state)
        original_ledger = copy.deepcopy(ledger)

        result = ledger_reconciliation.reconcile_terminal_ledger(state, ledger)

        self.assertEqual(result["decision"], "task-passed")
        self.assertEqual(result["monitor_action"], "pause")
        self.assertIsNone(result["state"]["active_task"])
        self.assertEqual(result["state"]["last_passed_task"], "task-a")
        self.assertEqual(result["state"]["last_processed_commit"], "abc123")
        self.assertEqual(result["state"]["last_processed_event"], "task-a:attempt-1:pass")
        self.assertEqual(result["state"]["marker"], {"preserve": True})
        self.assertEqual(state, original_state)
        self.assertEqual(ledger, original_ledger)
        self.assertTrue(orchestration_state.validate_state(result["state"]))

    def test_pass_can_arm_next_task(self):
        state = make_state()
        result = ledger_reconciliation.reconcile_terminal_ledger(
            state, pass_ledger(), next_task_id="task-b"
        )

        self.assertEqual(result["decision"], "task-passed-next-armed")
        self.assertEqual(result["monitor_action"], "rearm")
        next_state = result["state"]
        self.assertEqual(next_state["last_passed_task"], "task-a")
        self.assertEqual(next_state["active_task"], "task-b")
        self.assertEqual(next_state["active_attempt"], 1)
        self.assertEqual(next_state["pending_action"], "await-agent")
        self.assertEqual(next_state["retry_count"], 0)
        self.assertFalse(next_state["human_required"])
        self.assertIsNone(next_state["last_processed_commit"])
        self.assertEqual(next_state["last_processed_event"], "task-a:attempt-1:pass")
        self.assertEqual(next_state["marker"], {"preserve": True})
        self.assertTrue(orchestration_state.validate_state(next_state))

        with self.assertRaises(ValueError):
            ledger_reconciliation.reconcile_terminal_ledger(
                make_state(), pass_ledger(), next_task_id="   "
            )

    def test_duplicate_reconciliation_is_noop_after_completion(self):
        first = ledger_reconciliation.reconcile_terminal_ledger(
            make_state(), pass_ledger()
        )["state"]
        replay = ledger_reconciliation.reconcile_terminal_ledger(first, pass_ledger())
        self.assertEqual(replay["decision"], "duplicate")
        self.assertEqual(replay["monitor_action"], "noop")
        self.assertEqual(replay["state"], first)
        self.assertIsNot(replay["state"], first)

    def test_new_ledger_must_match_active_task_and_attempt(self):
        with self.assertRaises(ValueError):
            ledger_reconciliation.reconcile_terminal_ledger(
                make_state("task-a"), pass_ledger("task-b")
            )

        state = make_state("task-a")
        state["active_attempt"] = 2
        with self.assertRaises(ValueError):
            ledger_reconciliation.reconcile_terminal_ledger(
                state, pass_ledger("task-a", 1)
            )

    def test_human_required_reconciliation(self):
        state = make_state()
        ledger = pass_ledger()
        ledger["status"] = "human-required"

        result = ledger_reconciliation.reconcile_terminal_ledger(
            state, ledger, next_task_id="task-b"
        )

        self.assertEqual(result["decision"], "human-required")
        self.assertEqual(result["monitor_action"], "pause")
        self.assertEqual(result["state"]["active_task"], "task-a")
        self.assertTrue(result["state"]["human_required"])
        self.assertEqual(result["state"]["pending_action"], "human")
        self.assertEqual(
            result["state"]["last_processed_event"],
            "task-a:attempt-1:human-required",
        )
        self.assertEqual(result["state"]["last_processed_commit"], "abc123")
        self.assertTrue(orchestration_state.validate_state(result["state"]))

    def test_monitor_lifecycle_actions(self):
        active = make_state()
        self.assertEqual(
            ledger_reconciliation.monitor_lifecycle_action(
                active, monitor_enabled=True, matching_monitor_count=1
            ),
            "noop",
        )
        self.assertEqual(
            ledger_reconciliation.monitor_lifecycle_action(
                active, monitor_enabled=False, matching_monitor_count=1
            ),
            "rearm",
        )
        self.assertEqual(
            ledger_reconciliation.monitor_lifecycle_action(
                active, monitor_enabled=False, matching_monitor_count=0
            ),
            "rearm",
        )

        completed = orchestration_state.complete_task(make_state())
        self.assertEqual(
            ledger_reconciliation.monitor_lifecycle_action(
                completed, monitor_enabled=False, matching_monitor_count=1
            ),
            "pause",
        )

        human = make_state()
        human["human_required"] = True
        human["pending_action"] = "human"
        self.assertEqual(
            ledger_reconciliation.monitor_lifecycle_action(
                human, monitor_enabled=False, matching_monitor_count=1
            ),
            "human",
        )

        for count in (-1, 2):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    ledger_reconciliation.monitor_lifecycle_action(
                        active, monitor_enabled=False, matching_monitor_count=count
                    )


if __name__ == "__main__":
    unittest.main()
