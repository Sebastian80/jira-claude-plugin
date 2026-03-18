"""
Priority reference data.

Endpoints:
- GET /priorities - List all priority levels
"""

from fastapi import APIRouter, Depends, Query

from ..deps import jira
from ..response import formatted, jira_error_handler, OutputFormat, FORMAT_QUERY

router = APIRouter()


@router.get("/priorities")
@jira_error_handler()
def list_priorities(
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """List all priority levels."""
    priorities = client.get_all_priorities()
    return formatted(priorities, format, "priorities")
