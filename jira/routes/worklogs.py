"""
Worklog operations (time tracking).

Endpoints:
- GET /worklogs/{key} - List worklogs on issue
- POST /worklog/{key} - Add worklog (log time)
- GET /worklog/{key}/{worklog_id} - Get specific worklog
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from requests import HTTPError

from ..deps import jira
from ..response import success, formatted, formatted_error, get_status_code, is_status

router = APIRouter()


class AddWorklogBody(BaseModel):
    timeSpent: str
    comment: str | None = None
    started: str | None = None


@router.get("/worklogs/{key}")
async def list_worklogs(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List worklogs on issue."""
    try:
        result = client.issue_get_worklog(key)
        worklogs = result.get("worklogs", [])
        return formatted(worklogs, format, "worklogs")
    except HTTPError as e:
        if is_status(e, 404):
            return formatted_error(f"Issue {key} not found", fmt=format, status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/worklog/{key}")
async def add_worklog(key: str, body: AddWorklogBody, client=Depends(jira)):
    """Add worklog to issue."""
    from datetime import datetime

    # Validate timeSpent is not empty
    if not body.timeSpent or not body.timeSpent.strip():
        raise HTTPException(status_code=400, detail="timeSpent cannot be empty. Use format like '2h', '1d 4h', '30m'")

    try:
        # Build worklog payload for REST API
        worklog = {"timeSpent": body.timeSpent}
        if body.comment:
            worklog["comment"] = body.comment
        if body.started:
            worklog["started"] = body.started
        else:
            # Default to now in Jira's expected format
            worklog["started"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000")

        result = client.issue_add_json_worklog(key, worklog)
        return success(result)
    except HTTPError as e:
        if is_status(e, 404):
            raise HTTPException(status_code=404, detail=f"Issue {key} not found")
        if is_status(e, 400):
            raise HTTPException(status_code=400, detail=f"{e}. Use format like '2h', '1d 4h', '30m'")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/worklog/{key}/{worklog_id}")
async def get_worklog(
    key: str,
    worklog_id: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get specific worklog by ID."""
    try:
        url = f"rest/api/2/issue/{key}/worklog/{worklog_id}"
        worklog = client.get(url)
        return formatted(worklog, format, "worklog")
    except HTTPError as e:
        if is_status(e, 404):
            return formatted_error(f"Worklog {worklog_id} not found on issue {key}", fmt=format, status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
