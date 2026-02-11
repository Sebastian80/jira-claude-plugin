"""
User operations.

Get information about users in Jira.

Endpoints:
- GET /user - Get current authenticated user
- GET /user/me - Get current authenticated user (alias)
"""

from fastapi import APIRouter, Depends, Query

from ..deps import jira
from ..response import formatted, jira_error_handler

router = APIRouter()


@router.get("/user")
@router.get("/user/me")
@jira_error_handler()
async def get_user(
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get current authenticated user."""
    user = client.myself()
    return formatted(user, format, "user")
