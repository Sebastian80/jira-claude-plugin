"""
Watcher operations.

Endpoints:
- GET /watchers/{key} - List watchers on issue
- POST /watcher/{key} - Add watcher to issue
- DELETE /watcher/{key}/{username} - Remove watcher from issue
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from requests import HTTPError

from ..deps import jira
from ..response import success, error, formatted, formatted_error, get_status_code, is_status

router = APIRouter()


@router.get("/watchers/{key}")
async def list_watchers(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List watchers on issue."""
    try:
        watchers = client.issue_get_watchers(key)
        return formatted(watchers, format, "watchers")
    except HTTPError as e:
        if is_status(e, 404):
            return formatted_error(f"Issue {key} not found", fmt=format, status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watcher/{key}")
async def add_watcher(
    key: str,
    username: str = Query(..., description="Username of user to add as watcher"),
    client=Depends(jira),
):
    """Add watcher to issue."""
    try:
        client.issue_add_watcher(key, username)
        return success({"issue_key": key, "username": username, "added": True})
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Issue {key} not found")
        if is_status(e, 403):
            return error("Permission denied")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watcher/{key}/{username}")
async def remove_watcher(key: str, username: str, client=Depends(jira)):
    """Remove watcher from issue."""
    try:
        client.issue_delete_watcher(key, username)
        return success({"issue_key": key, "username": username, "removed": True})
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Issue {key} or watcher {username} not found")
        if is_status(e, 403):
            return error("Permission denied")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
