"""
Attachment operations.

Endpoints:
- GET /attachments/{key} - List attachments on issue
- POST /attachment/{key} - Upload attachment
- DELETE /attachment/{attachment_id} - Delete attachment
"""

import base64

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from requests import HTTPError

from ..deps import jira
from ..response import success, error, formatted, formatted_error, get_status_code, is_status

router = APIRouter()


class UploadAttachmentBody(BaseModel):
    filename: str
    content: str


@router.get("/attachments/{key}")
async def list_attachments(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List attachments on issue."""
    try:
        issue = client.issue(key, fields="attachment")
        attachments = issue.get("fields", {}).get("attachment", [])
        return formatted(attachments, format, "attachments")
    except HTTPError as e:
        if is_status(e, 404):
            return formatted_error(f"Issue {key} not found", fmt=format, status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attachment/{key}")
async def upload_attachment(key: str, body: UploadAttachmentBody, client=Depends(jira)):
    """Upload attachment to issue."""
    try:
        try:
            file_data = base64.b64decode(body.content)
        except Exception:
            return error("Failed to decode base64 content")

        result = client.add_attachment(issue_key=key, filename=body.filename, attachment=file_data)
        return success(result)
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Issue {key} not found")
        if is_status(e, 403):
            return error("Permission denied")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/attachment/{attachment_id}")
async def delete_attachment(attachment_id: str, client=Depends(jira)):
    """Delete attachment."""
    try:
        client.delete_attachment(attachment_id)
        return success({"attachment_id": attachment_id, "deleted": True})
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Attachment {attachment_id} not found", status=404)
        if is_status(e, 403):
            return error("Permission denied")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
