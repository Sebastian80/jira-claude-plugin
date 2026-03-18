"""
Attachment operations.

Endpoints:
- GET /attachments/{key} - List attachments on issue
- POST /attachment/{key} - Upload attachment(s) by local file path
- DELETE /attachment/{attachment_id} - Delete attachment
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..deps import jira
from ..response import success, error, formatted, jira_error_handler, OutputFormat, FORMAT_QUERY

router = APIRouter()

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


class UploadRequest(BaseModel):
    files: list[str]


@router.get("/attachments/{key}")
@jira_error_handler(not_found="Issue {key} not found")
def list_attachments(
    key: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """List attachments on issue."""
    issue = client.issue(key, fields="attachment")
    attachments = issue.get("fields", {}).get("attachment", [])
    return formatted(attachments, format, "attachments")


@router.post("/attachment/{key}")
@jira_error_handler(not_found="Issue {key} not found", forbidden="Permission denied")
def upload_attachment(
    key: str,
    body: UploadRequest,
    client=Depends(jira),
):
    """Upload attachment(s) to issue from local file paths."""
    # Validate all files before uploading any
    for file_path in body.files:
        path = Path(file_path)
        if not path.is_file():
            return error(f"File not found: {file_path}", status=404)
        file_size = path.stat().st_size
        if file_size > MAX_UPLOAD_SIZE:
            return error(
                f"File too large: {path.name} ({file_size} bytes). "
                f"Maximum upload size is {MAX_UPLOAD_SIZE // (1024 * 1024)}MB.",
                status=413,
            )

    results = []
    for file_path in body.files:
        result = client.add_attachment(issue_key=key, filename=file_path)
        results.extend(result)
    return success(results)


@router.delete("/attachment/{attachment_id}")
@jira_error_handler(not_found="Attachment {attachment_id} not found", forbidden="Permission denied")
def delete_attachment(attachment_id: str, client=Depends(jira)):
    """Delete attachment."""
    client.remove_attachment(attachment_id)
    return success({"attachment_id": attachment_id, "deleted": True})
