"""
Attachment operations.

Endpoints:
- GET /attachments/{key} - List attachments on issue
- POST /attachment/{key} - Upload attachment
- DELETE /attachment/{attachment_id} - Delete attachment
"""

import io

from fastapi import APIRouter, Depends, Query, UploadFile, File

from ..deps import jira
from ..response import success, error, formatted, jira_error_handler

router = APIRouter()


@router.get("/attachments/{key}")
@jira_error_handler(not_found="Issue {key} not found")
async def list_attachments(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List attachments on issue."""
    issue = client.issue(key, fields="attachment")
    attachments = issue.get("fields", {}).get("attachment", [])
    return formatted(attachments, format, "attachments")


@router.post("/attachment/{key}")
@jira_error_handler(not_found="Issue {key} not found", forbidden="Permission denied")
async def upload_attachment(
    key: str,
    file: UploadFile = File(...),
    client=Depends(jira)
):
    """Upload attachment to issue using multipart form-data."""
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

    # Wrap in BytesIO to set .name for the multipart Content-Disposition header
    # (SpooledTemporaryFile.name is read-only)
    content = file.file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        return error(
            f"File too large ({len(content)} bytes). Maximum upload size is {MAX_UPLOAD_SIZE // (1024 * 1024)}MB.",
            status=413,
        )
    upload = io.BytesIO(content)
    upload.name = file.filename
    result = client.add_attachment_object(issue_key=key, attachment=upload)
    return success(result)


@router.delete("/attachment/{attachment_id}")
@jira_error_handler(not_found="Attachment {attachment_id} not found", forbidden="Permission denied")
async def delete_attachment(attachment_id: str, client=Depends(jira)):
    """Delete attachment."""
    client.remove_attachment(attachment_id)
    return success({"attachment_id": attachment_id, "deleted": True})
