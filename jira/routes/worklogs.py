"""
Worklog operations (time tracking).

Endpoints:
- GET /worklogs/{key} - List worklogs on issue
- POST /worklog/{key} - Add worklog (log time)
- GET /worklog/{key}/{worklog_id} - Get specific worklog
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..deps import jira, user_timezone
from ..response import success, formatted, jira_error_handler, OutputFormat, FORMAT_QUERY

router = APIRouter()


class AddWorklogBody(BaseModel):
    timeSpent: str
    comment: str | None = None
    started: str | None = None


@router.get("/worklogs/{key}")
@jira_error_handler(not_found="Issue {key} not found")
def list_worklogs(
    key: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """List worklogs on issue."""
    result = client.issue_get_worklog(key)
    worklogs = result.get("worklogs", [])
    return formatted(worklogs, format, "worklogs")


@router.post("/worklog/{key}")
@jira_error_handler(
    not_found="Issue {key} not found",
    bad_request="Invalid time format. Use format like '2h', '1d 4h', '30m'",
)
def add_worklog(key: str, body: AddWorklogBody, client=Depends(jira)):
    """Add worklog to issue."""
    # Validate timeSpent is not empty
    if not body.timeSpent or not body.timeSpent.strip():
        raise HTTPException(status_code=400, detail="timeSpent cannot be empty. Use format like '2h', '1d 4h', '30m'")

    # Build worklog payload for REST API
    worklog = {"timeSpent": body.timeSpent}
    if body.comment:
        worklog["comment"] = body.comment
    if body.started:
        worklog["started"] = body.started
    else:
        # Default to now in the user's Jira timezone
        now = datetime.now(user_timezone())
        worklog["started"] = now.strftime("%Y-%m-%dT%H:%M:%S.000%z")
        # Format %z gives +0100, Jira expects +0100 (no colon) — already correct

    result = client.issue_add_json_worklog(key, worklog)
    return success(result)


@router.get("/worklog/{key}/{worklog_id}")
@jira_error_handler(not_found="Worklog {worklog_id} not found on issue {key}")
def get_worklog(
    key: str,
    worklog_id: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """Get specific worklog by ID."""
    url = f"rest/api/2/issue/{key}/worklog/{worklog_id}"
    worklog = client.get(url)
    return formatted(worklog, format, "worklog")
