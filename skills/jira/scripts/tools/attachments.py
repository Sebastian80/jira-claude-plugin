"""
Attachment tools - File attachment operations.

Tools:
- GetAttachments: Get issue attachments
- AddAttachment: Add attachment to issue
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetAttachments", "AddAttachment"]


class GetAttachments(Tool):
    """Get attachments for an issue."""

    key: str = Field(..., description="Issue key")
    format: str = Field("json", description="Output format: json, human")

    class Meta:
        method = "GET"
        path = "/attachments/{key}"
        tags = ["attachments"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            issue = ctx.client.issue(self.key, fields="attachment")
            attachments = issue.get("fields", {}).get("attachment", [])
            return formatted(attachments, self.format, "attachments")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class AddAttachment(Tool):
    """Add attachment to an issue."""

    key: str = Field(..., description="Issue key")
    file_path: str = Field(..., alias="file", description="Path to file to attach")

    class Meta:
        method = "POST"
        path = "/attachment/{key}"
        tags = ["attachments"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            result = ctx.client.add_attachment(self.key, self.file_path)
            return {"success": True, "data": result}
        except Exception as e:
            return ToolResult(error=str(e), status=400)
