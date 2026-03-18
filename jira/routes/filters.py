"""
Saved filter operations.

Endpoints:
- GET /filters - List your favorite filters
- GET /filter/{filter_id} - Get filter details including JQL
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from requests import HTTPError

from ..deps import jira
from ..response import formatted, get_status_code, is_status, jira_error_handler, OutputFormat, FORMAT_QUERY

# Note: list_filters uses manual try/except instead of @jira_error_handler
# because 404 means "no favorites" (return empty list), not an error.

router = APIRouter()


@router.get("/filters")
def list_filters(
    format: OutputFormat = FORMAT_QUERY,
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
def get_filter(
    filter_id: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """Get filter details."""
    filter_data = client.get_filter(filter_id)
    return formatted(filter_data, format, "filter")
