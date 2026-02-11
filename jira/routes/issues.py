"""
Issue CRUD operations.

Core operations for working with Jira issues: viewing, creating, and updating.

Endpoints:
- GET /issue/{key} - Get issue details with optional field filtering
- POST /create - Create new issue with required and optional fields
- PATCH /issue/{key} - Update specific fields on existing issue
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, model_validator

from ..deps import jira
from ..response import success, formatted, jira_error_handler

router = APIRouter()


class CreateIssueBody(BaseModel):
    project: str
    summary: str
    type: str
    description: str | None = None
    priority: str | None = None
    labels: str | None = None
    assignee: str | None = None
    parent: str | None = None
    custom: str | None = None


class UpdateIssueBody(BaseModel):
    summary: str | None = None
    description: str | None = None
    priority: str | None = None
    labels: str | None = None
    assignee: str | None = None
    custom: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not any([self.summary, self.description, self.priority,
                     self.labels, self.assignee, self.custom]):
            raise ValueError("At least one field must be provided")
        return self


@router.get("/issue/{key}")
@jira_error_handler(not_found="Issue {key} not found")
async def get_issue(
    key: str,
    fields: str | None = Query(None, description="Comma-separated fields to return"),
    expand: str | None = Query(None, description="Fields to expand (e.g., 'changelog')"),
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get issue details by key."""
    params = {}
    if fields:
        params["fields"] = fields
    if expand:
        params["expand"] = expand

    issue = client.issue(key, **params)
    return formatted(issue, format, "issue")


@router.post("/create")
@jira_error_handler()
async def create_issue(body: CreateIssueBody, client=Depends(jira)):
    """Create new issue in Jira."""
    issue_fields = {
        "project": {"key": body.project},
        "summary": body.summary,
        "issuetype": {"name": body.type},
    }
    if body.description:
        issue_fields["description"] = body.description
    if body.priority:
        issue_fields["priority"] = {"name": body.priority}
    if body.labels:
        issue_fields["labels"] = [label.strip() for label in body.labels.split(",")]
    if body.assignee:
        if "@" in body.assignee:
            issue_fields["assignee"] = {"emailAddress": body.assignee}
        else:
            issue_fields["assignee"] = {"name": body.assignee}
    if body.parent:
        issue_fields["parent"] = {"key": body.parent}
    if body.custom:
        try:
            custom_fields = json.loads(body.custom)
            issue_fields.update(custom_fields)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in custom fields: {e}")

    result = client.create_issue(fields=issue_fields)
    return success(result)


@router.get("/show/{key}")
@jira_error_handler(not_found="Issue {key} not found")
async def show_issue(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get issue with comments combined in one view."""
    # Fetch issue with comment field included
    issue = client.issue(key, fields="*all,comment")

    # Extract comments from issue response
    comments = issue.get("fields", {}).get("comment", {}).get("comments", [])

    # Remove comments from fields to avoid duplication
    if "fields" in issue and "comment" in issue["fields"]:
        del issue["fields"]["comment"]

    # Combine into single response
    combined = {
        "issue": issue,
        "comments": list(reversed(comments)),  # Most recent first
    }
    return formatted(combined, format, "show")


@router.delete("/delete/{key}")
@jira_error_handler(not_found="Issue {key} not found")
async def delete_issue(
    key: str,
    client=Depends(jira),
):
    """Delete an issue permanently."""
    client.delete_issue(key)
    return success({"key": key, "deleted": True})


@router.patch("/issue/{key}")
@jira_error_handler()
async def update_issue(key: str, body: UpdateIssueBody, client=Depends(jira)):
    """Update issue fields."""
    update_fields = {}

    if body.summary:
        update_fields["summary"] = body.summary
    if body.description:
        update_fields["description"] = body.description
    if body.priority:
        update_fields["priority"] = {"name": body.priority}
    if body.labels:
        update_fields["labels"] = [label.strip() for label in body.labels.split(",")]
    if body.assignee:
        if "@" in body.assignee:
            update_fields["assignee"] = {"emailAddress": body.assignee}
        else:
            update_fields["assignee"] = {"name": body.assignee}
    if body.custom:
        try:
            custom_fields = json.loads(body.custom)
            update_fields.update(custom_fields)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in custom fields: {e}")

    client.update_issue_field(key, update_fields)
    return success({"key": key, "updated": list(update_fields.keys())})
