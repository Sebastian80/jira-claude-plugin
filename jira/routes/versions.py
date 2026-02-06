"""
Version/Release operations.

Endpoints:
- GET /versions/{project} - List versions in project
- POST /version - Create version
- GET /version/{version_id} - Get version details
- PATCH /version/{version_id} - Update version
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from requests import HTTPError

from ..deps import jira
from ..response import success, error, formatted, get_status_code, is_status

router = APIRouter()


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
async def create_version(
    project: str = Query(..., description="Project key"),
    name: str = Query(..., description="Version name"),
    description: str = Query(None, description="Version description"),
    released: bool = Query(False, description="Mark as released"),
    client=Depends(jira),
):
    """Create a version."""
    try:
        result = client.create_version(
            name=name, project=project, description=description, released=released
        )
        return success(result)
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Project '{project}' not found")
        if is_status(e, 409):
            return error(f"Version '{name}' already exists in {project}")
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
async def update_version(
    version_id: str,
    name: str = Query(None, description="New version name"),
    description: str = Query(None, description="New description"),
    released: bool = Query(None, description="Release status"),
    client=Depends(jira),
):
    """Update a version."""
    if name is None and description is None and released is None:
        return error("At least one field must be provided")

    try:
        result = client.update_version(
            version_id=version_id, name=name, description=description, released=released
        )
        return success(result)
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Version '{version_id}' not found", status=404)
        if is_status(e, 409):
            return error(f"Version name '{name}' already exists")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
