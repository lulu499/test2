APP_VERSION = "0.1.0"

BUILD_INFO = {"version": APP_VERSION, "status": "ready"}


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
    """Return application build metadata."""
    return BUILD_INFO
