"""
Link tools - Issue links and web links.

Tools:
- GetLinks: Get issue links
- GetLinkTypes: Get available link types
- CreateIssueLink: Link two issues
- CreateWebLink: Add web link to issue
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetLinks", "GetLinkTypes", "CreateIssueLink", "CreateWebLink"]


class GetLinks(Tool):
    """Get links for an issue."""

    key: str = Field(..., description="Issue key")
    format: str = Field("ai", description="Output format: json, rich, ai")

    class Meta:
        method = "GET"
        path = "/links/{key}"
        tags = ["links"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            issue = ctx.client.issue(self.key, fields="issuelinks")
            links = issue.get("fields", {}).get("issuelinks", [])
            return formatted(links, self.format, "links")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class GetLinkTypes(Tool):
    """Get available issue link types."""

    class Meta:
        method = "GET"
        path = "/linktypes"
        tags = ["links"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            link_types = ctx.client.get_issue_link_types()
            return ToolResult(data=link_types)
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class CreateIssueLink(Tool):
    """Create link between two issues."""

    inward_issue: str = Field(..., alias="inward", description="Inward issue key")
    outward_issue: str = Field(..., alias="outward", description="Outward issue key")
    link_type: str = Field(..., alias="type", description="Link type name (e.g., 'Blocks')")
    comment: str | None = Field(None, description="Optional comment")

    class Meta:
        method = "POST"
        path = "/link"
        tags = ["links"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            data = {
                "type": {"name": self.link_type},
                "inwardIssue": {"key": self.inward_issue},
                "outwardIssue": {"key": self.outward_issue},
            }
            if self.comment:
                data["comment"] = {"body": self.comment}

            ctx.client.create_issue_link(data)
            return ToolResult(data={"inward": self.inward_issue, "outward": self.outward_issue}, status=201)
        except Exception as e:
            return ToolResult(error=str(e), status=400)


class CreateWebLink(Tool):
    """Add web link to an issue."""

    key: str = Field(..., description="Issue key")
    url: str = Field(..., description="URL to link")
    title: str = Field(..., description="Link title")

    class Meta:
        method = "POST"
        path = "/weblink/{key}"
        tags = ["links"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            result = ctx.client.create_or_update_issue_remote_links(
                self.key,
                self.url,
                self.title
            )
            return ToolResult(data=result, status=201)
        except Exception as e:
            return ToolResult(error=str(e), status=400)
