"""
Issue tools - CRUD operations for Jira issues.

Tools:
- GetIssue: Get issue details by key
- CreateIssue: Create new issue
- UpdateIssue: Update issue fields
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted, formatted_error

__all__ = ["GetIssue", "CreateIssue", "UpdateIssue"]


class GetIssue(Tool):
    """Get issue details by key."""

    key: str = Field(..., description="Issue key like PROJ-123")
    fields: str | None = Field(None, description="Comma-separated fields to return")
    expand: str | None = Field(None, description="Fields to expand (e.g., 'changelog')")
    format: str = Field("ai", description="Output format: json, human, ai, markdown")

    class Meta:
        method = "GET"
        path = "/issue/{key}"
        tags = ["issues"]

    async def execute(self, ctx: ToolContext) -> Any:
        params = {}
        if self.fields:
            params["fields"] = self.fields
        if self.expand:
            params["expand"] = self.expand

        try:
            issue = ctx.client.issue(self.key, **params)
            return formatted(issue, self.format, "issue")
        except Exception as e:
            if "does not exist" in str(e).lower() or "404" in str(e):
                return formatted_error(f"Issue {self.key} not found", fmt=self.format, status=404)
            return ToolResult(error=str(e), status=500)


class CreateIssue(Tool):
    """Create new issue in Jira."""

    project: str = Field(..., description="Project key")
    summary: str = Field(..., description="Issue title/summary")
    issue_type: str = Field(..., alias="type", description="Issue type: Story, Bug, Task, etc.")
    description: str | None = Field(None, description="Issue description")
    priority: str | None = Field(None, description="Priority: Highest, High, Medium, Low, Lowest")
    labels: str | None = Field(None, description="Comma-separated labels")
    assignee: str | None = Field(None, description="Username or email of assignee")
    parent: str | None = Field(None, description="Parent issue key (for subtasks)")

    class Meta:
        method = "POST"
        path = "/create"
        tags = ["issues"]

    async def execute(self, ctx: ToolContext) -> Any:
        issue_fields = {
            "project": {"key": self.project},
            "summary": self.summary,
            "issuetype": {"name": self.issue_type},
        }

        if self.description:
            issue_fields["description"] = self.description
        if self.priority:
            issue_fields["priority"] = {"name": self.priority}
        if self.labels:
            issue_fields["labels"] = [label.strip() for label in self.labels.split(",")]
        if self.assignee:
            if "@" in self.assignee:
                issue_fields["assignee"] = {"emailAddress": self.assignee}
            else:
                issue_fields["assignee"] = {"name": self.assignee}
        if self.parent:
            issue_fields["parent"] = {"key": self.parent}

        try:
            result = ctx.client.create_issue(fields=issue_fields)
            return {"success": True, "data": result}
        except Exception as e:
            return ToolResult(error=str(e), status=400)


class UpdateIssue(Tool):
    """Update issue fields."""

    key: str = Field(..., description="Issue key to update")
    summary: str | None = Field(None, description="New issue summary/title")
    priority: str | None = Field(None, description="Priority: Highest, High, Medium, Low, Lowest")
    labels: str | None = Field(None, description="Comma-separated labels (replaces existing)")
    assignee: str | None = Field(None, description="Username or email of assignee")

    class Meta:
        method = "PATCH"
        path = "/issue/{key}"
        tags = ["issues"]

    async def execute(self, ctx: ToolContext) -> Any:
        update_fields = {}

        if self.summary:
            update_fields["summary"] = self.summary
        if self.priority:
            update_fields["priority"] = {"name": self.priority}
        if self.labels:
            update_fields["labels"] = [label.strip() for label in self.labels.split(",")]
        if self.assignee:
            if "@" in self.assignee:
                update_fields["assignee"] = {"emailAddress": self.assignee}
            else:
                update_fields["assignee"] = {"name": self.assignee}

        if not update_fields:
            return {"success": False, "error": "No fields specified to update"}

        try:
            ctx.client.update_issue_field(self.key, update_fields)
            return {"success": True, "data": {"key": self.key, "updated": list(update_fields.keys())}}
        except Exception as e:
            return ToolResult(error=str(e), status=500)
