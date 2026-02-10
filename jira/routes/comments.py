"""
Comment operations.

Endpoints:
- POST /comment/{key} - Add comment to issue
- GET /comments/{key} - List comments on issue
- DELETE /comment/{key}/{comment_id} - Delete comment from issue
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from requests import HTTPError

from ..deps import jira
from ..response import success, error, formatted, formatted_error, get_status_code, is_status

router = APIRouter()


class AddCommentBody(BaseModel):
    text: str


@router.post("/comment/{key}")
async def add_comment(key: str, body: AddCommentBody, client=Depends(jira)):
    """Add comment to issue."""
    try:
        result = client.issue_add_comment(key, body.text)
        return success(result)
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Issue {key} not found", status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comments/{key}")
async def list_comments(
    key: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum comments to return"),
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List comments on issue."""
    try:
        issue = client.issue(key, fields="comment")
        comments = issue.get("fields", {}).get("comment", {}).get("comments", [])
        return formatted(list(reversed(comments))[:limit], format, "comments")
    except HTTPError as e:
        if is_status(e, 404):
            return formatted_error(f"Issue {key} not found", fmt=format, status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/comment/{key}/{comment_id}")
async def delete_comment(key: str, comment_id: str, client=Depends(jira)):
    """Delete a comment from an issue."""
    try:
        client.delete(f"rest/api/2/issue/{key}/comment/{comment_id}")
        return success({"key": key, "comment_id": comment_id, "deleted": True})
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Comment {comment_id} not found on issue {key}", status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
