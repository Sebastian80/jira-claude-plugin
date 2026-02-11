"""
Version/Release operations.

Endpoints:
- GET /versions/{project} - List versions in project
- POST /version - Create version
- GET /version/{version_id} - Get version details
- PATCH /version/{version_id} - Update version
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, model_validator

from ..deps import jira
from ..response import success, formatted, jira_error_handler

router = APIRouter()


class CreateVersionBody(BaseModel):
    project: str
    name: str
    description: str | None = None
    released: bool = False


class UpdateVersionBody(BaseModel):
    name: str | None = None
    description: str | None = None
    released: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.name is None and self.description is None and self.released is None:
            raise ValueError("At least one field must be provided")
        return self


@router.get("/versions/{project}")
@jira_error_handler(not_found="Project '{project}' not found")
async def list_versions(
    project: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List versions in a project."""
    versions = client.get_project_versions(project)
    return formatted(versions, format, "versions")


@router.post("/version")
@jira_error_handler(
    not_found="Project '{project}' not found",
    conflict="Version '{name}' already exists in {project}",
)
async def create_version(body: CreateVersionBody, client=Depends(jira)):
    """Create a version."""
    result = client.create_version(
        name=body.name, project=body.project, description=body.description, released=body.released
    )
    return success(result)


@router.get("/version/{version_id}")
@jira_error_handler(not_found="Version '{version_id}' not found")
async def get_version(
    version_id: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get version details."""
    version = client.get_version(version_id)
    return formatted(version, format, "version")


@router.patch("/version/{version_id}")
@jira_error_handler(
    not_found="Version '{version_id}' not found",
    conflict="Version name '{name}' already exists",
)
async def update_version(version_id: str, body: UpdateVersionBody, client=Depends(jira)):
    """Update a version."""
    result = client.update_version(
        version_id=version_id, name=body.name, description=body.description, released=body.released
    )
    return success(result)
