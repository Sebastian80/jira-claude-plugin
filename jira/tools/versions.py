"""
Version tools - Project version/release operations.

Tools:
- GetVersions: List versions in a project
- GetVersion: Get version details
- CreateVersion: Create a new version
- UpdateVersion: Update existing version
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetVersions", "GetVersion", "CreateVersion", "UpdateVersion"]


class GetVersions(Tool):
    """List versions in a project."""

    project: str = Field(..., description="Project key")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/versions/{project}"
        tags = ["versions"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            versions = ctx.client.get_project_versions(self.project)
            return formatted(versions, self.format, "versions")
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                return ToolResult(error=f"Project '{self.project}' not found", status=404)
            return ToolResult(error=str(e), status=500)


class GetVersion(Tool):
    """Get version details."""

    version_id: str = Field(..., alias="id", description="Version ID")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/version/{version_id}"
        tags = ["versions"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            version = ctx.client.get_version(self.version_id)
            return formatted(version, self.format, "version")
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                return ToolResult(error=f"Version '{self.version_id}' not found", status=404)
            return ToolResult(error=str(e), status=500)


class CreateVersion(Tool):
    """Create a version in a project."""

    project: str = Field(..., description="Project key")
    name: str = Field(..., description="Version name")
    description: str | None = Field(None, description="Version description")
    released: bool = Field(False, description="Mark as released")

    class Meta:
        method = "POST"
        path = "/version"
        tags = ["versions"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            result = ctx.client.create_version(
                name=self.name,
                project=self.project,
                description=self.description,
                released=self.released,
            )
            return ToolResult(data=result)
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                return ToolResult(error=f"Project '{self.project}' not found", status=404)
            if "already exists" in error_msg:
                return ToolResult(error=f"Version '{self.name}' already exists in {self.project}", status=400)
            return ToolResult(error=str(e), status=500)


class UpdateVersion(Tool):
    """Update a version."""

    version_id: str = Field(..., alias="id", description="Version ID")
    name: str | None = Field(None, description="New version name")
    description: str | None = Field(None, description="New description")
    released: bool | None = Field(None, description="Release status")

    class Meta:
        method = "PATCH"
        path = "/version/{version_id}"
        tags = ["versions"]

    async def execute(self, ctx: ToolContext) -> Any:
        if self.name is None and self.description is None and self.released is None:
            return ToolResult(error="At least one field must be provided", status=400)

        try:
            result = ctx.client.update_version(
                version_id=self.version_id,
                name=self.name,
                description=self.description,
                released=self.released,
            )
            return ToolResult(data=result)
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                return ToolResult(error=f"Version '{self.version_id}' not found", status=404)
            if "already exists" in error_msg:
                return ToolResult(error=f"Version name '{self.name}' already exists", status=400)
            return ToolResult(error=str(e), status=500)
