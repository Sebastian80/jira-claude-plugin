"""
FastAPI dependencies for Jira routes.

Standalone version - no bridge dependency.
Uses module-level singleton for Jira client.

Usage:
    from fastapi import Depends
    from .deps import jira

    @router.get("/issue/{key}")
    async def get_issue(key: str, client=Depends(jira)):
        return client.issue(key)
"""

from fastapi import HTTPException

from .lib.client import get_jira_client

# Module-level singleton
_client = None
_healthy = False
_error = None


def init_client():
    """Initialize the Jira client singleton."""
    global _client, _healthy, _error
    try:
        _client = get_jira_client()
        # Verify connection
        _client.myself()
        _healthy = True
        _error = None
    except Exception as e:
        _client = None
        _healthy = False
        _error = str(e)
        raise


def get_client():
    """Get the Jira client, initializing if needed."""
    global _client, _healthy
    if _client is None:
        init_client()
    return _client


def is_healthy() -> bool:
    """Check if client is healthy."""
    return _healthy and _client is not None


def get_error() -> str | None:
    """Get last error message."""
    return _error


def jira():
    """FastAPI dependency - get Jira client.

    Raises HTTPException if client not available.
    """
    try:
        client = get_client()
        return client
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Jira not connected: {e}"
        )


def reset():
    """Reset client (for testing or reconnection)."""
    global _client, _healthy, _error
    _client = None
    _healthy = False
    _error = None
