"""
Jira Agile/Sprint operations.

Operations for working with Jira Software sprints and boards.

Endpoints:
- GET /sprints/{board_id} - List sprints for a board
- GET /sprint/{sprint_id} - Get sprint details
- POST /sprint/{sprint_id}/issues - Add issues to sprint
- DELETE /sprint/{sprint_id}/issues - Remove issues from sprint
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import jira
from ..response import success, error

router = APIRouter()


@router.get("/boards")
async def list_boards(
    project: str | None = Query(None, description="Filter by project key"),
    board_type: str | None = Query(None, alias="type", description="Filter by type: scrum, kanban"),
    client=Depends(jira),
):
    """List all boards."""
    try:
        params = {}
        if project:
            params["projectKeyOrId"] = project
        if board_type:
            params["type"] = board_type

        # Use raw request to Agile API
        result = client.get("rest/agile/1.0/board", params=params)
        return success(result.get("values", []))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sprints/{board_id}")
async def list_sprints(
    board_id: int,
    state: str | None = Query(None, description="Filter by state: active, future, closed"),
    client=Depends(jira),
):
    """List sprints for a board."""
    try:
        params = {}
        if state:
            params["state"] = state

        result = client.get(f"rest/agile/1.0/board/{board_id}/sprint", params=params)
        return success(result.get("values", []))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sprint/{sprint_id}")
async def get_sprint(
    sprint_id: int,
    client=Depends(jira),
):
    """Get sprint details."""
    try:
        result = client.get(f"rest/agile/1.0/sprint/{sprint_id}")
        return success(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sprint/{sprint_id}/issues")
async def add_issues_to_sprint(
    sprint_id: int,
    issues: str = Query(..., description="Comma-separated issue keys to add"),
    client=Depends(jira),
):
    """Add issues to a sprint."""
    try:
        issue_keys = [k.strip() for k in issues.split(",")]

        result = client.post(
            f"rest/agile/1.0/sprint/{sprint_id}/issue",
            json={"issues": issue_keys}
        )
        return success({"sprint_id": sprint_id, "added": issue_keys})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sprint/{sprint_id}/issues")
async def remove_issues_from_sprint(
    sprint_id: int,
    issues: str = Query(..., description="Comma-separated issue keys to remove"),
    client=Depends(jira),
):
    """Remove issues from sprint (moves to backlog)."""
    try:
        issue_keys = [k.strip() for k in issues.split(",")]

        # Moving to backlog removes from sprint
        result = client.post(
            "rest/agile/1.0/backlog/issue",
            json={"issues": issue_keys}
        )
        return success({"removed_from_sprint": sprint_id, "moved_to_backlog": issue_keys})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sprint/active/{project}")
async def get_active_sprint(
    project: str,
    client=Depends(jira),
):
    """Get the active sprint for a project."""
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
