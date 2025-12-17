"""
Comment tools - Issue comments operations.

Tools:
- GetComments: Get comments on an issue
- AddComment: Add comment to an issue
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetComments", "AddComment"]


class GetComments(Tool):
    """Get comments on an issue."""

    key: str = Field(..., description="Issue key")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/comments/{key}"
        tags = ["comments"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            result = ctx.client.issue_get_comments(self.key)
            comments = result.get("comments", [])
            return formatted(comments, self.format, "comments")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class AddComment(Tool):
    """Add comment to an issue."""

    key: str = Field(..., description="Issue key")
    body: str = Field(..., description="Comment text")

    class Meta:
        method = "POST"
        path = "/comment/{key}"
        tags = ["comments"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            result = ctx.client.issue_add_comment(self.key, self.body)
            return ToolResult(data=result, status=201)
        except Exception as e:
            return ToolResult(error=str(e), status=400)
