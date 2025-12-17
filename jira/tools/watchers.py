"""
Watcher tools - Issue watcher operations.

Tools:
- GetWatchers: List watchers on an issue
- AddWatcher: Add watcher to an issue
- RemoveWatcher: Remove watcher from an issue
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetWatchers", "AddWatcher", "RemoveWatcher"]


class GetWatchers(Tool):
    """Get watchers for an issue."""

    key: str = Field(..., description="Issue key")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/watchers/{key}"
        tags = ["watchers"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            watchers = ctx.client.issue_get_watchers(self.key)
            return formatted(watchers, self.format, "watchers")
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "404" in error_msg:
                return ToolResult(error=f"Issue {self.key} not found", status=404)
            return ToolResult(error=str(e), status=500)


class AddWatcher(Tool):
    """Add watcher to an issue."""

    key: str = Field(..., description="Issue key")
    username: str = Field(..., description="Username of user to add as watcher")

    class Meta:
        method = "POST"
        path = "/watcher/{key}"
        tags = ["watchers"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            ctx.client.issue_add_watcher(self.key, self.username)
            return ToolResult(data={"issue_key": self.key, "username": self.username, "added": True})
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "404" in error_msg:
                return ToolResult(error=f"Issue {self.key} not found", status=404)
            if "user" in error_msg and "not found" in error_msg:
                return ToolResult(error=f"User {self.username} not found", status=400)
            if "permission" in error_msg:
                return ToolResult(error="Permission denied", status=403)
            return ToolResult(error=str(e), status=500)


class RemoveWatcher(Tool):
    """Remove watcher from an issue."""

    key: str = Field(..., description="Issue key")
    username: str = Field(..., description="Username of watcher to remove")

    class Meta:
        method = "DELETE"
        path = "/watcher/{key}/{username}"
        tags = ["watchers"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            ctx.client.issue_delete_watcher(self.key, self.username)
            return ToolResult(data={"issue_key": self.key, "username": self.username, "removed": True})
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "404" in error_msg:
                return ToolResult(error=f"Issue {self.key} or watcher {self.username} not found", status=404)
            if "permission" in error_msg:
                return ToolResult(error="Permission denied", status=403)
            return ToolResult(error=str(e), status=500)
