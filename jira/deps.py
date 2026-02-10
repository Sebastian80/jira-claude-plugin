"""
FastAPI dependencies for Jira routes.

Creates a fresh Jira client per request to avoid stale connection issues.
The overhead (~100ms) is negligible for CLI usage.
"""

from fastapi import HTTPException

from .lib.client import get_jira_client


def init_client():
    """Compatibility stub - no-op since we create fresh clients per request."""
    # Verify connection works on startup
    client = get_jira_client()
    client.myself()


def reset():
    """Compatibility stub - no-op since we don't maintain state."""
    pass


def jira():
    """FastAPI dependency - get fresh Jira client per request."""
    try:
        return get_jira_client()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Jira not connected: {e}"
        )


def check_health() -> dict:
    """Check Jira connection health in a single API call."""
    try:
        client = get_jira_client()
        client.myself()
        return {"healthy": True}
    except Exception as e:
        return {"healthy": False, "error": str(e)}
