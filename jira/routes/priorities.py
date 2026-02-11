"""
Priority reference data.

Endpoints:
- GET /priorities - List all priority levels
"""

from fastapi import APIRouter, Depends, Query

from ..deps import jira
from ..response import formatted, jira_error_handler

router = APIRouter()


@router.get("/priorities")
@jira_error_handler()
async def list_priorities(
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List all priority levels."""
    priorities = client.get_all_priorities()
    return formatted(priorities, format, "priorities")
