"""
Component tools - Project component operations.

Tools:
- GetComponents: List components in a project
- GetComponent: Get component details
- CreateComponent: Create a new component
- UpdateComponent: Update existing component (via DeleteComponent recreate if needed)
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetComponents", "GetComponent", "CreateComponent", "DeleteComponent"]


class GetComponents(Tool):
    """List components in a project."""

    project: str = Field(..., description="Project key")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/components/{project}"
        tags = ["components"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            components = ctx.client.get_project_components(self.project)
            return formatted(components, self.format, "components")
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                return ToolResult(error=f"Project '{self.project}' not found", status=404)
            return ToolResult(error=str(e), status=500)


class GetComponent(Tool):
    """Get component details."""

    component_id: str = Field(..., alias="id", description="Component ID")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/component/{component_id}"
        tags = ["components"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            component = ctx.client.component(self.component_id)
            return formatted(component, self.format, "component")
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                return ToolResult(error=f"Component '{self.component_id}' not found", status=404)
            return ToolResult(error=str(e), status=500)


class CreateComponent(Tool):
    """Create a component in a project."""

    project: str = Field(..., description="Project key")
    name: str = Field(..., description="Component name")
    description: str | None = Field(None, description="Component description")
    lead: str | None = Field(None, description="Component lead username")

    class Meta:
        method = "POST"
        path = "/component"
        tags = ["components"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            component = {"name": self.name, "project": self.project}
            if self.description:
                component["description"] = self.description
            if self.lead:
                component["leadUserName"] = self.lead

            result = ctx.client.create_component(component)
            return ToolResult(data=result)
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                return ToolResult(error=f"Project '{self.project}' not found", status=404)
            if "already exists" in error_msg:
                return ToolResult(error=f"Component '{self.name}' already exists in {self.project}", status=400)
            return ToolResult(error=str(e), status=500)


class DeleteComponent(Tool):
    """Delete a component."""

    component_id: str = Field(..., alias="id", description="Component ID to delete")

    class Meta:
        method = "DELETE"
        path = "/component/{component_id}"
        tags = ["components"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            ctx.client.delete_component(self.component_id)
            return ToolResult(data={"deleted": True, "component_id": self.component_id})
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                return ToolResult(error=f"Component '{self.component_id}' not found", status=404)
            return ToolResult(error=str(e), status=500)
