"""
Version/Release operations.

Endpoints:
- GET /versions/{project} - List versions in project
- POST /version - Create version
- GET /version/{version_id} - Get version details
- PATCH /version/{version_id} - Update version
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, model_validator
from requests import HTTPError

from ..deps import jira
from ..response import success, error, formatted, get_status_code, is_status

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
async def list_versions(
    project: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List versions in a project."""
    try:
        versions = client.get_project_versions(project)
        return formatted(versions, format, "versions")
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Project '{project}' not found", status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/version")
async def create_version(body: CreateVersionBody, client=Depends(jira)):
    """Create a version."""
    try:
        result = client.create_version(
            name=body.name, project=body.project, description=body.description, released=body.released
        )
        return success(result)
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Project '{body.project}' not found")
        if is_status(e, 409):
            return error(f"Version '{body.name}' already exists in {body.project}")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/version/{version_id}")
async def get_version(
    version_id: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get version details."""
    try:
        version = client.get_version(version_id)
        return formatted(version, format, "version")
    except HTTPError as e:
        if is_status(e, 404):
            raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/version/{version_id}")
async def update_version(version_id: str, body: UpdateVersionBody, client=Depends(jira)):
    """Update a version."""
    try:
        result = client.update_version(
            version_id=version_id, name=body.name, description=body.description, released=body.released
        )
        return success(result)
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Version '{version_id}' not found", status=404)
        if is_status(e, 409):
            return error(f"Version name '{body.name}' already exists")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
