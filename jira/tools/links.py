"""
Link tools - Issue links and web links.

Tools:
- GetLinks: Get issue links for an issue
- GetLinkTypes: Get available link types in the Jira instance
- GetWebLinks: Get web/remote links attached to an issue
- CreateIssueLink: Link two issues together
- CreateWebLink: Add a web link to an issue
"""

from typing import Any

from atlassian.errors import ApiNotFoundError
from pydantic import Field
from requests import HTTPError

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetLinks", "GetLinkTypes", "CreateIssueLink", "CreateWebLink", "GetWebLinks"]


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


class GetWebLinks(Tool):
    """Get web/remote links for an issue.

    Retrieves all external URLs attached to an issue as remote links.
    These are typically links to external resources like documentation,
    related PRs, or external tracking systems.

    Example:
        jira weblinks PROJ-123
        jira weblinks PROJ-123 --format json
    """

    key: str = Field(..., description="Issue key")
    format: str = Field("ai", description="Output format: json, rich, ai")

    class Meta:
        method = "GET"
        path = "/weblinks/{key}"
        tags = ["links"]

    async def execute(self, ctx: ToolContext) -> Any:
        """Fetch remote links from Jira API.

        Args:
            ctx: Tool context with Jira client and formatter.

        Returns:
            Formatted list of web links or ToolResult on error.

        Raises:
            ToolResult with 404 if issue not found.
            ToolResult with 500 for other errors.
        """
        try:
            links = ctx.client.get_issue_remote_links(self.key)
            return formatted(links, self.format, "weblinks")
        except ApiNotFoundError:
            return ToolResult(error=f"Issue {self.key} not found", status=404)
        except HTTPError as e:
            # Check HTTP status code from requests library
            if hasattr(e, "response") and e.response is not None:
                if e.response.status_code == 404:
                    return ToolResult(error=f"Issue {self.key} not found", status=404)
            return ToolResult(error=str(e), status=500)
        except Exception as e:
            return ToolResult(error=str(e), status=500)


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
