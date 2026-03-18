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
from ..response import success, formatted, jira_error_handler, OutputFormat, FORMAT_QUERY

router = APIRouter()


def _apply_optional_fields(body, fields: dict) -> None:
    """Apply shared optional fields (description, priority, labels, assignee, custom) to a fields dict."""
    if body.description is not None:
        fields["description"] = body.description
    if body.priority is not None:
        fields["priority"] = {"name": body.priority}
    if body.labels is not None:
        fields["labels"] = [label.strip() for label in body.labels.split(",")]
    if body.assignee is not None:
        if "@" in body.assignee:
            fields["assignee"] = {"emailAddress": body.assignee}
        else:
            fields["assignee"] = {"name": body.assignee}
    if body.custom is not None:
        try:
            custom_fields = json.loads(body.custom)
            fields.update(custom_fields)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in custom fields: {e}")


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
        if all(v is None for v in [self.summary, self.description, self.priority,
                                    self.labels, self.assignee, self.custom]):
            raise ValueError("At least one field must be provided")
        return self


@router.get("/issue/{key}")
@jira_error_handler(not_found="Issue {key} not found")
def get_issue(
    key: str,
    fields: str | None = Query(None, description="Comma-separated fields to return"),
    expand: str | None = Query(None, description="Fields to expand (e.g., 'changelog')"),
    format: OutputFormat = FORMAT_QUERY,
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
def create_issue(body: CreateIssueBody, client=Depends(jira)):
    """Create new issue in Jira."""
    issue_fields = {
        "project": {"key": body.project},
        "summary": body.summary,
        "issuetype": {"name": body.type},
    }
    if body.parent is not None:
        issue_fields["parent"] = {"key": body.parent}
    _apply_optional_fields(body, issue_fields)

    result = client.create_issue(fields=issue_fields)
    return success(result)


@router.get("/show/{key}")
@jira_error_handler(not_found="Issue {key} not found")
def show_issue(
    key: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """Get issue with comments combined in one view."""
    # Fetch issue with the fields the formatters actually use, plus comments
    issue = client.issue(key, fields="summary,status,issuetype,priority,assignee,reporter,labels,description,comment")

    # Extract comments, then build issue without comment field to avoid duplication
    fields = issue.get("fields", {})
    comments = fields.get("comment", {}).get("comments", [])
    issue_without_comments = {**issue, "fields": {k: v for k, v in fields.items() if k != "comment"}}

    combined = {
        "issue": issue_without_comments,
        "comments": list(reversed(comments)),  # Most recent first
    }
    return formatted(combined, format, "show")


@router.delete("/delete/{key}")
@jira_error_handler(not_found="Issue {key} not found")
def delete_issue(
    key: str,
    client=Depends(jira),
):
    """Delete an issue permanently."""
    client.delete_issue(key)
    return success({"key": key, "deleted": True})


@router.patch("/issue/{key}")
@jira_error_handler()
def update_issue(key: str, body: UpdateIssueBody, client=Depends(jira)):
    """Update issue fields."""
    update_fields = {}
    if body.summary is not None:
        update_fields["summary"] = body.summary
    _apply_optional_fields(body, update_fields)

    client.update_issue_field(key, update_fields)
    return success({"key": key, "updated": list(update_fields.keys())})
