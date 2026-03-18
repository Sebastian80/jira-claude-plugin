"""
FastAPI dependencies for Jira routes.

Caches a single Jira client for the lifetime of the server process.
The atlassian-python-api library uses requests.Session internally,
which handles connection pooling and keep-alive.
"""

import logging
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from .lib.client import get_jira_client

logger = logging.getLogger(__name__)

_client = None
_user_tz: ZoneInfo = ZoneInfo("UTC")


def init_client():
    """Create and cache the Jira client and user timezone at startup."""
    global _client, _user_tz
    _client = get_jira_client()
    user = _client.myself()
    tz_name = user.get("timeZone")
    if tz_name:
        try:
            _user_tz = ZoneInfo(tz_name)
            logger.info("User timezone: %s", tz_name)
        except KeyError:
            logger.warning("Unknown timezone '%s', using UTC", tz_name)


def jira():
    """FastAPI dependency — return the cached Jira client."""
    if _client is None:
        raise HTTPException(status_code=503, detail="Jira client not initialized")
    return _client


def user_timezone() -> ZoneInfo:
    """Return the Jira user's timezone (from their profile)."""
    return _user_tz
