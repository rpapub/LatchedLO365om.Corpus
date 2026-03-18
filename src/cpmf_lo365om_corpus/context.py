"""Template context creation and substitution."""

import uuid
from datetime import datetime, timezone


def make_context(run_id: str, timestamp: str, date: str, label: str = "", index: int = 0) -> dict:
    return {
        "run_id":       run_id,
        "run_id_short": run_id[:8],
        "timestamp":    timestamp,
        "date":         date,
        "label":        label,
        "index":        index,
        "row_index":    0,
    }


def t(value, ctx: dict, row_index: int = 0) -> str:
    """Substitute template variables in a string value."""
    if not isinstance(value, str):
        return value
    return value.format_map({**ctx, "row_index": row_index})


def t_deep(value, ctx: dict):
    """Recursively substitute template variables in nested dicts, lists, and strings."""
    if isinstance(value, str):
        return t(value, ctx)
    if isinstance(value, dict):
        return {k: t_deep(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [t_deep(item, ctx) for item in value]
    return value


def make_run_context() -> tuple[str, str, str]:
    """Generate run_id, timestamp, date for a new corpus run."""
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    return run_id, now.strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y%m%d")
