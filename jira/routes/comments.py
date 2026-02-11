"""
Comment operations.

Endpoints:
- POST /comment/{key} - Add comment to issue
- GET /comments/{key} - List comments on issue
- DELETE /comment/{key}/{comment_id} - Delete comment from issue
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..deps import jira
from ..response import success, formatted, jira_error_handler

router = APIRouter()


class AddCommentBody(BaseModel):
    text: str


@router.post("/comment/{key}")
@jira_error_handler(not_found="Issue {key} not found")
async def add_comment(key: str, body: AddCommentBody, client=Depends(jira)):
    """Add comment to issue."""
    result = client.issue_add_comment(key, body.text)
    return success(result)


@router.get("/comments/{key}")
@jira_error_handler(not_found="Issue {key} not found")
async def list_comments(
    key: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum comments to return"),
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List comments on issue."""
    issue = client.issue(key, fields="comment")
    comments = issue.get("fields", {}).get("comment", {}).get("comments", [])
    return formatted(list(reversed(comments))[:limit], format, "comments")


@router.delete("/comment/{key}/{comment_id}")
@jira_error_handler(not_found="Comment {comment_id} not found on issue {key}")
async def delete_comment(key: str, comment_id: str, client=Depends(jira)):
    """Delete a comment from an issue."""
    client.delete(f"rest/api/2/issue/{key}/comment/{comment_id}")
    return success({"key": key, "comment_id": comment_id, "deleted": True})
