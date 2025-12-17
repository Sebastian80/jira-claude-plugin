"""
Project tools - Project operations.

Tools:
- GetProjects: List all projects
- GetProject: Get project details
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetProjects", "GetProject"]


class GetProjects(Tool):
    """List all Jira projects."""

    include_archived: bool = Field(False, alias="includeArchived", description="Include archived projects")
    expand: str | None = Field(None, description="Fields to expand")
    format: str = Field("json", description="Output format: json, human, ai, markdown")

    class Meta:
        method = "GET"
        path = "/projects"
        tags = ["projects"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            kwargs = {}
            if self.include_archived:
                kwargs["included_archived"] = True
            if self.expand:
                kwargs["expand"] = self.expand

            projects = ctx.client.projects(**kwargs)
            return formatted(projects, self.format, "projects")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class GetProject(Tool):
    """Get project details by key."""

    key: str = Field(..., description="Project key")
    format: str = Field("json", description="Output format: json, human, ai, markdown")

    class Meta:
        method = "GET"
        path = "/project/{key}"
        tags = ["projects"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            project = ctx.client.project(self.key)
            return formatted(project, self.format, "project")
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "404" in error_msg:
                return ToolResult(error=f"Project {self.key} not found", status=404)
            return ToolResult(error=str(e), status=500)
