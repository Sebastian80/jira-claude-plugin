"""
Project operations.

Endpoints:
- GET /projects - List all projects
- GET /project/{key} - Get project details
- GET /project/{key}/components - Get project components
- GET /project/{key}/versions - Get project versions
"""

from fastapi import APIRouter, Depends, Query

from ..deps import jira
from ..response import formatted, jira_error_handler

router = APIRouter()


@router.get("/projects")
@jira_error_handler()
async def list_projects(
    include_archived: bool = Query(False, alias="includeArchived", description="Include archived projects"),
    expand: str | None = Query(None, description="Fields to expand"),
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List all Jira projects."""
    kwargs = {}
    if include_archived:
        kwargs["included_archived"] = True
    if expand:
        kwargs["expand"] = expand

    projects = client.projects(**kwargs)
    return formatted(projects, format, "projects")


@router.get("/project/{key}")
@jira_error_handler(not_found="Project {key} not found")
async def get_project(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get project details by key."""
    project = client.project(key)
    return formatted(project, format, "project")


@router.get("/project/{key}/components")
async def get_project_components(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get project components (delegates to /components/{project})."""
    from .components import list_components
    return await list_components(key, format, client)


@router.get("/project/{key}/versions")
async def get_project_versions(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """Get project versions (delegates to /versions/{project})."""
    from .versions import list_versions
    return await list_versions(key, format, client)
