import copy
from typing import Any

from orchestration_state import (
    attempt_key,
    begin_auto_correction,
    complete_task,
    record_processed_commit,
    should_process_commit,
    validate_state,
)

CI_STATUSES = (None, "queued", "in_progress", "success", "failure", "cancelled")
REVIEW_OUTCOMES = (None, "pass", "mechanical-failure", "human-required")

_CI_PENDING = (None, "queued", "in_progress")
_CI_TERMINAL = ("success", "failure", "cancelled")


def _copy_state(state: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(state)


def _unchanged(decision: str, state: dict[str, Any]) -> dict[str, Any]:
    return {"decision": decision, "state": _copy_state(state)}


def _has_active_task(state: dict[str, Any]) -> bool:
    active_task = state.get("active_task")
    return isinstance(active_task, str) and bool(active_task.strip())


def _missing_commit(candidate_commit: str | None) -> bool:
    return candidate_commit is None or not str(candidate_commit).strip()


def _advance_to_review(state: dict[str, Any]) -> dict[str, Any]:
    result = _copy_state(state)
    result["pending_action"] = "review"
    validate_state(result)
    return result


def _escalate_to_human(state: dict[str, Any]) -> dict[str, Any]:
    result = _copy_state(state)
    result["pending_action"] = "human"
    result["human_required"] = True
    validate_state(result)
    return result


def process_monitor_observation(
    state: dict[str, Any],
    *,
    candidate_commit: str | None = None,
    ci_status: str | None = None,
    review_outcome: str | None = None,
) -> dict[str, Any]:
    validate_state(state)
    if ci_status not in CI_STATUSES:
        raise ValueError("unsupported ci_status")
    if review_outcome not in REVIEW_OUTCOMES:
        raise ValueError("unsupported review_outcome")

    if state["human_required"] or state["pending_action"] == "human":
        return _unchanged("human-required", state)

    if not _has_active_task(state):
        return _unchanged("noop", state)

    pending_action = state["pending_action"]

    if pending_action == "await-agent":
        if _missing_commit(candidate_commit) or not should_process_commit(
            state, candidate_commit
        ):
            return _unchanged("noop", state)
        return {
            "decision": "commit-recorded",
            "state": record_processed_commit(
                state, candidate_commit, pending_action="await-ci"
            ),
        }

    if pending_action == "await-ci":
        recorded = state.get("last_processed_commit")
        if not isinstance(recorded, str) or not recorded.strip():
            raise ValueError("await-ci requires last_processed_commit")
        if ci_status in _CI_PENDING:
            return _unchanged("ci-pending", state)
        if ci_status in _CI_TERMINAL:
            return {"decision": "ready-for-review", "state": _advance_to_review(state)}

    if pending_action == "review":
        if review_outcome is None:
            return _unchanged("noop", state)
        if review_outcome == "pass":
            return {"decision": "task-passed", "state": complete_task(state)}
        if review_outcome == "human-required":
            return {"decision": "human-required", "state": _escalate_to_human(state)}
        if review_outcome == "mechanical-failure":
            next_state = begin_auto_correction(state)
            if next_state["human_required"]:
                return {"decision": "human-required", "state": next_state}
            return {
                "decision": "dispatch-correction",
                "state": next_state,
                "attempt_key": attempt_key(
                    next_state["active_task"], next_state["active_attempt"]
                ),
            }

    return _unchanged("noop", state)
