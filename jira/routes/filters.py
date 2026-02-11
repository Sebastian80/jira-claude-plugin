"""
Saved filter operations.

Endpoints:
- GET /filters - List your favorite filters
- GET /filter/{filter_id} - Get filter details including JQL
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from requests import HTTPError

from ..deps import jira
from ..response import formatted, get_status_code, is_status, jira_error_handler

router = APIRouter()


@router.get("/filters")
async def list_filters(
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List your favorite filters."""
    try:
        filters = client.get("rest/api/2/filter/favourite")
        return formatted(filters, format, "filters")
    except HTTPError as e:
        if is_status(e, 404):
            return formatted([], format, "filters")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filter/{filter_id}")
@jira_error_handler()
async def get_filter(
    filter_id: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get filter details."""
    filter_data = client.get_filter(filter_id)
    return formatted(filter_data, format, "filter")
