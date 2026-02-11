"""
Jira Agile/Sprint operations.

Operations for working with Jira Software sprints and boards.

Endpoints:
- GET /sprints/{board_id} - List sprints for a board
- GET /sprint/{sprint_id} - Get sprint details
- POST /sprint/{sprint_id}/issues - Add issues to sprint
- DELETE /sprint/{sprint_id}/issues - Remove issues from sprint
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..deps import jira
from ..response import success, error, jira_error_handler

router = APIRouter()


class SprintIssuesBody(BaseModel):
    issues: str


@router.get("/boards")
@jira_error_handler(not_found="No boards found")
async def list_boards(
    project: str | None = Query(None, description="Filter by project key"),
    board_type: str | None = Query(None, alias="type", description="Filter by type: scrum, kanban"),
    client=Depends(jira),
):
    """List all boards."""
    params = {}
    if project:
        params["projectKeyOrId"] = project
    if board_type:
        params["type"] = board_type

    # Use raw request to Agile API
    result = client.get("rest/agile/1.0/board", params=params)
    return success(result.get("values", []))


@router.get("/sprints/{board_id}")
@jira_error_handler(not_found="Board {board_id} not found")
async def list_sprints(
    board_id: int,
    state: str | None = Query(None, description="Filter by state: active, future, closed"),
    client=Depends(jira),
):
    """List sprints for a board."""
    params = {}
    if state:
        params["state"] = state

    result = client.get(f"rest/agile/1.0/board/{board_id}/sprint", params=params)
    return success(result.get("values", []))


@router.get("/sprint/{sprint_id}")
@jira_error_handler(not_found="Sprint {sprint_id} not found")
async def get_sprint(
    sprint_id: int,
    client=Depends(jira),
):
    """Get sprint details."""
    result = client.get(f"rest/agile/1.0/sprint/{sprint_id}")
    return success(result)


@router.post("/sprint/{sprint_id}/issues")
@jira_error_handler(not_found="Sprint {sprint_id} not found")
async def add_issues_to_sprint(sprint_id: int, body: SprintIssuesBody, client=Depends(jira)):
    """Add issues to a sprint."""
    issue_keys = [k.strip() for k in body.issues.split(",")]

    result = client.post(
        f"rest/agile/1.0/sprint/{sprint_id}/issue",
        json={"issues": issue_keys}
    )
    return success({"sprint_id": sprint_id, "added": issue_keys})


@router.delete("/sprint/{sprint_id}/issues")
@jira_error_handler()
async def remove_issues_from_sprint(
    sprint_id: int,
    issues: str = Query(..., description="Comma-separated issue keys to remove"),
    client=Depends(jira),
):
    """Remove issues from sprint (moves to backlog)."""
    issue_keys = [k.strip() for k in issues.split(",")]

    # Moving to backlog removes from sprint
    result = client.post(
        "rest/agile/1.0/backlog/issue",
        json={"issues": issue_keys}
    )
    return success({"removed_from_sprint": sprint_id, "moved_to_backlog": issue_keys})


@router.get("/sprint/active/{project}")
@jira_error_handler(not_found="No boards found for project {project}")
async def get_active_sprint(
    project: str,
    client=Depends(jira),
):
    """Get the active sprint for a project."""
    # First find boards for the project
    boards = client.get("rest/agile/1.0/board", params={"projectKeyOrId": project})
    board_list = boards.get("values", [])

    if not board_list:
        return error(f"No boards found for project {project}")

    # Get active sprint from first board
    board_id = board_list[0]["id"]
    sprints = client.get(
        f"rest/agile/1.0/board/{board_id}/sprint",
        params={"state": "active"}
    )
    sprint_list = sprints.get("values", [])

    if not sprint_list:
        return error(f"No active sprint found for project {project}")

    return success(sprint_list[0])
