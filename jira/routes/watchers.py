"""
Watcher operations.

Endpoints:
- GET /watchers/{key} - List watchers on issue
- POST /watcher/{key} - Add watcher to issue
- DELETE /watcher/{key}/{username} - Remove watcher from issue
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..deps import jira
from ..response import success, formatted, jira_error_handler, OutputFormat, FORMAT_QUERY

router = APIRouter()


class AddWatcherBody(BaseModel):
    username: str


@router.get("/watchers/{key}")
@jira_error_handler(not_found="Issue {key} not found")
def list_watchers(
    key: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """List watchers on issue."""
    watchers = client.issue_get_watchers(key)
    return formatted(watchers, format, "watchers")


@router.post("/watcher/{key}")
@jira_error_handler(not_found="Issue {key} not found", forbidden="Permission denied")
def add_watcher(key: str, body: AddWatcherBody, client=Depends(jira)):
    """Add watcher to issue."""
    client.issue_add_watcher(key, body.username)
    return success({"issue_key": key, "username": body.username, "added": True})


@router.delete("/watcher/{key}/{username}")
@jira_error_handler(not_found="Issue {key} or watcher {username} not found", forbidden="Permission denied")
def remove_watcher(key: str, username: str, client=Depends(jira)):
    """Remove watcher from issue."""
    client.issue_delete_watcher(key, username)
    return success({"issue_key": key, "username": username, "removed": True})
