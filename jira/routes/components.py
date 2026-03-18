"""
Component operations.

Endpoints:
- GET /components/{project} - List components in project
- POST /component - Create component
- GET /component/{component_id} - Get component details
- DELETE /component/{component_id} - Delete component
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..deps import jira
from ..response import success, formatted, jira_error_handler, OutputFormat, FORMAT_QUERY

router = APIRouter()


class CreateComponentBody(BaseModel):
    project: str
    name: str
    description: str | None = None
    lead: str | None = None


@router.get("/components/{project}")
@jira_error_handler(not_found="Project '{project}' not found")
def list_components(
    project: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """List components in a project."""
    components = client.get_project_components(project)
    return formatted(components, format, "components")


@router.post("/component")
@jira_error_handler(
    not_found="Project '{project}' not found",
    conflict="Component '{name}' already exists in {project}",
)
def create_component(body: CreateComponentBody, client=Depends(jira)):
    """Create a component."""
    component = {"name": body.name, "project": body.project}
    if body.description:
        component["description"] = body.description
    if body.lead:
        component["leadUserName"] = body.lead

    result = client.create_component(component)
    return success(result)


@router.get("/component/{component_id}")
@jira_error_handler(not_found="Component '{component_id}' not found")
def get_component(
    component_id: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """Get component details."""
    component = client.component(component_id)
    return formatted(component, format, "component")


@router.delete("/component/{component_id}")
@jira_error_handler(not_found="Component '{component_id}' not found")
def delete_component(component_id: str, client=Depends(jira)):
    """Delete a component."""
    client.delete_component(component_id)
    return success({"deleted": True, "component_id": component_id})
