"""
Worklog tools - Time tracking operations.

Tools:
- GetWorklogs: List worklogs on an issue
- AddWorklog: Add time entry to an issue
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetWorklogs", "AddWorklog"]


class GetWorklogs(Tool):
    """Get worklogs for an issue."""

    key: str = Field(..., description="Issue key")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/worklogs/{key}"
        tags = ["worklogs"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            result = ctx.client.issue_get_worklog(self.key)
            worklogs = result.get("worklogs", [])
            return formatted(worklogs, self.format, "worklogs")
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "404" in error_msg:
                return ToolResult(error=f"Issue {self.key} not found", status=404)
            return ToolResult(error=str(e), status=500)


class AddWorklog(Tool):
    """Add worklog to an issue."""

    key: str = Field(..., description="Issue key")
    time_spent: str = Field(..., alias="timeSpent", description="Time spent (e.g., '1h 30m', '2d', '30m')")
    comment: str | None = Field(None, description="Work description")
    started: str | None = Field(None, description="Start time (ISO 8601 format)")

    class Meta:
        method = "POST"
        path = "/worklog/{key}"
        tags = ["worklogs"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            worklog = {"timeSpent": self.time_spent}
            if self.comment:
                worklog["comment"] = self.comment
            if self.started:
                worklog["started"] = self.started

            result = ctx.client.issue_add_json_worklog(self.key, worklog)
            return ToolResult(data=result, status=201)
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "404" in error_msg:
                return ToolResult(error=f"Issue {self.key} not found", status=404)
            if "time" in error_msg:
                return ToolResult(error=f"{e}. Use format like '2h', '1d 4h', '30m'", status=400)
            return ToolResult(error=str(e), status=500)
