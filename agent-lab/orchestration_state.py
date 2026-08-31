import copy
from typing import Any

PENDING_ACTIONS = (
    "await-agent",
    "await-ci",
    "review",
    "correct",
    "next-task",
    "human",
    None,
)

_REQUIRED_FIELDS = (
    "active_task",
    "active_attempt",
    "last_passed_task",
    "human_required",
    "last_processed_commit",
    "last_processed_event",
    "pending_action",
    "retry_count",
    "max_auto_retries",
)


def _require_task_id(task_id: str) -> str:
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("task_id must not be empty")
    return task_id


def _is_empty_sha(commit_sha: str) -> bool:
    return not isinstance(commit_sha, str) or not commit_sha.strip()


def _copy_state(state: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(state)


def validate_state(state: dict[str, Any]) -> bool:
    for field in _REQUIRED_FIELDS:
        if field not in state:
            raise ValueError(f"missing required field: {field}")
    if state["pending_action"] not in PENDING_ACTIONS:
        raise ValueError("invalid pending_action")
    if state["active_attempt"] < 1:
        raise ValueError("active_attempt must be >= 1")
    if state["retry_count"] < 0:
        raise ValueError("retry_count must not be negative")
    if state["max_auto_retries"] < 0:
        raise ValueError("max_auto_retries must not be negative")
    if state["retry_count"] > state["max_auto_retries"]:
        raise ValueError("retry_count exceeds max_auto_retries")
    if state["human_required"] and state["pending_action"] != "human":
        raise ValueError("human_required requires pending_action='human'")
    return True


def new_task_state(task_id: str, *, max_auto_retries: int = 2) -> dict[str, Any]:
    _require_task_id(task_id)
    if max_auto_retries < 0:
        raise ValueError("max_auto_retries must not be negative")
    state = {
        "active_task": task_id,
        "active_attempt": 1,
        "last_passed_task": None,
        "human_required": False,
        "last_processed_commit": None,
        "last_processed_event": None,
        "pending_action": "await-agent",
        "retry_count": 0,
        "max_auto_retries": max_auto_retries,
    }
    validate_state(state)
    return state


def attempt_key(task_id: str, attempt: int) -> str:
    _require_task_id(task_id)
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    return f"{task_id}:attempt-{attempt}"


def should_process_commit(state: dict[str, Any], commit_sha: str) -> bool:
    if _is_empty_sha(commit_sha):
        return False
    active_task = state.get("active_task")
    if not isinstance(active_task, str) or not active_task.strip():
        return False
    if commit_sha == state.get("last_processed_commit"):
        return False
    return True


def record_processed_commit(
    state: dict[str, Any],
    commit_sha: str,
    *,
    pending_action: str | None = "await-ci",
) -> dict[str, Any]:
    if _is_empty_sha(commit_sha):
        raise ValueError("commit_sha must not be empty")
    if pending_action not in PENDING_ACTIONS:
        raise ValueError("invalid pending_action")
    if state.get("last_processed_commit") == commit_sha:
        result = _copy_state(state)
        validate_state(result)
        return result
    result = _copy_state(state)
    result["last_processed_commit"] = commit_sha
    result["pending_action"] = pending_action
    validate_state(result)
    return result


def begin_auto_correction(state: dict[str, Any]) -> dict[str, Any]:
    result = _copy_state(state)
    if result["retry_count"] < result["max_auto_retries"]:
        result["retry_count"] += 1
        result["active_attempt"] += 1
        result["last_processed_commit"] = None
        result["last_processed_event"] = None
        result["pending_action"] = "await-agent"
        result["human_required"] = False
    else:
        result["pending_action"] = "human"
        result["human_required"] = True
    validate_state(result)
    return result


def complete_task(state: dict[str, Any]) -> dict[str, Any]:
    result = _copy_state(state)
    result["last_passed_task"] = result["active_task"]
    result["active_task"] = None
    result["pending_action"] = None
    result["human_required"] = False
    validate_state(result)
    return result
