"""
User tools - User operations.

Tools:
- GetCurrentUser: Get current authenticated user
- GetHealth: Check Jira connection health
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetCurrentUser", "GetHealth"]


class GetCurrentUser(Tool):
    """Get current authenticated user."""

    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/user/me"
        tags = ["user"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            user = ctx.client.myself()
            return formatted(user, self.format, "user")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class GetHealth(Tool):
    """Check Jira connection health."""

    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/health"
        tags = ["system"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            user = ctx.client.myself()
            health_data = {
                "status": "healthy",
                "connected": True,
                "user": user.get("displayName", user.get("name", "Unknown")),
                "email": user.get("emailAddress"),
                "server": getattr(ctx.client, "url", "Unknown"),
            }
            return formatted(health_data, self.format, "health")
        except Exception as e:
            health_data = {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }
            return formatted(health_data, self.format, "health")
