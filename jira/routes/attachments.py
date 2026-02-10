"""
Attachment operations.

Endpoints:
- GET /attachments/{key} - List attachments on issue
- POST /attachment/{key} - Upload attachment
- DELETE /attachment/{attachment_id} - Delete attachment
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from requests import HTTPError

from ..deps import jira
from ..response import success, error, formatted, formatted_error, get_status_code, is_status

router = APIRouter()


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
async def upload_attachment(
    key: str,
    file: UploadFile = File(...),
    client=Depends(jira)
):
    """Upload attachment to issue using multipart form-data."""
    try:
        # Wrap in BytesIO to set .name for the multipart Content-Disposition header
        # (SpooledTemporaryFile.name is read-only)
        import io
        content = file.file.read()
        upload = io.BytesIO(content)
        upload.name = file.filename
        result = client.add_attachment_object(issue_key=key, attachment=upload)
        return success(result)
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Issue {key} not found", status=404)
        if is_status(e, 403):
            return error("Permission denied", status=403)
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
