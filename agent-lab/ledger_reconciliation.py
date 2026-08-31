import copy
from typing import Any

from orchestration_state import (
    attempt_key,
    complete_task,
    record_processed_commit,
    validate_state,
)

TERMINAL_LEDGER_STATUSES = ("pass", "human-required")

_REQUIRED_LEDGER_FIELDS = (
    "task_id",
    "attempt",
    "attempt_key",
    "status",
    "processed_by_background_work",
)


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _has_active_task(state: dict[str, Any]) -> bool:
    active_task = state.get("active_task")
    return isinstance(active_task, str) and bool(active_task.strip())


def _require_commit_sha(ledger: dict[str, Any]) -> str:
    commit_sha = ledger.get("implementation_commit")
    if not isinstance(commit_sha, str) or not commit_sha.strip():
        raise ValueError("implementation_commit must not be empty")
    return commit_sha


def _validate_ledger(ledger: dict[str, Any]) -> None:
    for field in _REQUIRED_LEDGER_FIELDS:
        if field not in ledger:
            raise ValueError(f"missing required ledger field: {field}")
    if ledger["processed_by_background_work"] is not True:
        raise ValueError("ledger must be processed_by_background_work")
    if ledger["status"] not in TERMINAL_LEDGER_STATUSES:
        raise ValueError("ledger status must be terminal")
    expected_key = attempt_key(ledger["task_id"], ledger["attempt"])
    if ledger["attempt_key"] != expected_key:
        raise ValueError("attempt_key does not match task_id and attempt")


def ledger_event_id(ledger: dict[str, Any]) -> str:
    _validate_ledger(ledger)
    return f"{ledger['task_id']}:attempt-{ledger['attempt']}:{ledger['status']}"


def _result(decision: str, monitor_action: str, state: dict[str, Any]) -> dict[str, Any]:
    validate_state(state)
    return {
        "decision": decision,
        "monitor_action": monitor_action,
        "state": state,
    }


def _arm_next_task(completed: dict[str, Any], next_task_id: str) -> dict[str, Any]:
    if not isinstance(next_task_id, str) or not next_task_id.strip():
        raise ValueError("next_task_id must not be empty")
    armed = _copy(completed)
    armed["active_task"] = next_task_id.strip()
    armed["active_attempt"] = 1
    armed["pending_action"] = "await-agent"
    armed["retry_count"] = 0
    armed["human_required"] = False
    armed["last_processed_commit"] = None
    validate_state(armed)
    return armed


def reconcile_terminal_ledger(
    state: dict[str, Any],
    ledger: dict[str, Any],
    next_task_id: str | None = None,
) -> dict[str, Any]:
    validate_state(state)
    event_id = ledger_event_id(ledger)

    if state.get("last_processed_event") == event_id:
        return _result("duplicate", "noop", _copy(state))

    if state.get("active_task") != ledger["task_id"]:
        raise ValueError("ledger task_id does not match active_task")
    if state.get("active_attempt") != ledger["attempt"]:
        raise ValueError("ledger attempt does not match active_attempt")

    commit_sha = _require_commit_sha(ledger)

    if ledger["status"] == "human-required":
        next_state = record_processed_commit(
            state, commit_sha, pending_action="human"
        )
        next_state["human_required"] = True
        next_state["last_processed_event"] = event_id
        return _result("human-required", "pause", next_state)

    recorded = record_processed_commit(state, commit_sha, pending_action="review")
    recorded["last_processed_event"] = event_id
    completed = complete_task(recorded)

    if next_task_id is not None:
        armed = _arm_next_task(completed, next_task_id)
        return _result("task-passed-next-armed", "rearm", armed)

    return _result("task-passed", "pause", completed)


def monitor_lifecycle_action(
    state: dict[str, Any],
    *,
    monitor_enabled: bool,
    matching_monitor_count: int,
) -> str:
    validate_state(state)
    if matching_monitor_count not in (0, 1):
        raise ValueError("matching_monitor_count must be 0 or 1")
    if state["human_required"] or state["pending_action"] == "human":
        return "human"
    if not _has_active_task(state):
        return "pause"
    if matching_monitor_count == 1 and monitor_enabled:
        return "noop"
    return "rearm"
