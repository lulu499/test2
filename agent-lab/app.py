def greeting(name: str) -> str:
    """Return a deterministic greeting used by the orchestration lab."""
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("name must not be empty")
    return f"Hello, {cleaned}!"
