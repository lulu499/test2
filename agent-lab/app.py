from typing import Literal

APP_VERSION = "0.1.0"
ReadinessState = Literal["ready", "degraded", "maintenance"]
READINESS_STATES: tuple[ReadinessState, ...] = ("ready", "degraded", "maintenance")
_CURRENT_READINESS: ReadinessState = "ready"


def greeting(name: str) -> str:
    """Return a deterministic greeting used by the orchestration lab."""
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("name must not be empty")
    return f"Hello, {cleaned}!"


def version() -> str:
    """Return the stable application version."""
    return APP_VERSION


def build_info() -> dict:
    """Return a fresh copy of application build metadata."""
    return {"version": APP_VERSION, "status": "ready"}


def status() -> ReadinessState:
    """Return the public readiness status from the approved contract."""
    return _CURRENT_READINESS
