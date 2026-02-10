"""
Component operations.

Endpoints:
- GET /components/{project} - List components in project
- POST /component - Create component
- GET /component/{component_id} - Get component details
- DELETE /component/{component_id} - Delete component
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from requests import HTTPError

from ..deps import jira
from ..response import success, error, formatted, formatted_error, get_status_code, is_status

router = APIRouter()


class CreateComponentBody(BaseModel):
    project: str
    name: str
    description: str | None = None
    lead: str | None = None


@router.get("/components/{project}")
async def list_components(
    project: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List components in a project."""
    try:
        components = client.get_project_components(project)
        return formatted(components, format, "components")
    except HTTPError as e:
        if is_status(e, 404):
            return formatted_error(f"Project '{project}' not found", fmt=format, status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/component")
async def create_component(body: CreateComponentBody, client=Depends(jira)):
    """Create a component."""
    try:
        component = {"name": body.name, "project": body.project}
        if body.description:
            component["description"] = body.description
        if body.lead:
            component["leadUserName"] = body.lead

        result = client.create_component(component)
        return success(result)
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Project '{body.project}' not found", status=404)
        if is_status(e, 409):
            return error(f"Component '{body.name}' already exists in {body.project}", status=409)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/component/{component_id}")
async def get_component(
    component_id: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get component details."""
    try:
        component = client.component(component_id)
        return formatted(component, format, "component")
    except HTTPError as e:
        if is_status(e, 404):
            return formatted_error(f"Component '{component_id}' not found", fmt=format, status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/component/{component_id}")
async def delete_component(component_id: str, client=Depends(jira)):
    """Delete a component."""
    try:
        client.delete_component(component_id)
        return success({"deleted": True, "component_id": component_id})
    except HTTPError as e:
        if is_status(e, 404):
            return error(f"Component '{component_id}' not found", status=404)
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
