"""
Link operations (issue links and web links).

Endpoints:
- GET /links/{key} - List all links on an issue
- GET /linktypes - List available link types
- GET /link/types - List available link types (alias)
- POST /link - Create link between issues
- POST /weblink/{key} - Add web link to issue
- GET /weblinks/{key} - List web links on issue
- DELETE /weblink/{key}/{link_id} - Remove web link
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from requests import HTTPError

from ..deps import jira
from ..response import success, formatted, get_status_code, is_status

router = APIRouter()


class CreateLinkBody(BaseModel):
    from_key: str = Field(alias="from")
    to: str
    type: str

    model_config = {"populate_by_name": True}


class AddWeblinkBody(BaseModel):
    url: str
    title: str | None = None


@router.get("/links/{key}")
async def get_issue_links(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List all links on an issue."""
    try:
        issue = client.issue(key, fields="issuelinks")
        links = issue.get("fields", {}).get("issuelinks", [])
        return formatted(links, format, "links")
    except HTTPError as e:
        if is_status(e, 404):
            raise HTTPException(status_code=404, detail=f"Issue {key} not found")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/linktypes")
async def list_link_types_alias(
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List available issue link types."""
    try:
        types = client.get_issue_link_types()
        return formatted(types, format, "linktypes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/link")
async def create_link(body: CreateLinkBody, client=Depends(jira)):
    """Create link between two issues."""
    try:
        link_data = {
            "type": {"name": body.type},
            "inwardIssue": {"key": body.to},
            "outwardIssue": {"key": body.from_key},
        }
        client.create_issue_link(link_data)
        return success({"from": body.from_key, "to": body.to, "type": body.type})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/link/types")
async def list_link_types(client=Depends(jira)):
    """List available issue link types."""
    try:
        types = client.get_issue_link_types()
        return success(types)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weblink/{key}")
async def add_weblink(key: str, body: AddWeblinkBody, client=Depends(jira)):
    """Add web link to issue."""
    link_title = body.title or body.url
    try:
        link_object = {"url": body.url, "title": link_title}
        endpoint = f"rest/api/2/issue/{key}/remotelink"
        response = client._session.post(f"{client.url}/{endpoint}", json={"object": link_object})
        response.raise_for_status()
        result = response.json()
        return success({"key": key, "url": body.url, "title": link_title, "id": result.get("id")})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weblinks/{key}")
async def list_weblinks(
    key: str,
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List web links on issue."""
    try:
        endpoint = f"rest/api/2/issue/{key}/remotelink"
        response = client._session.get(f"{client.url}/{endpoint}")
        response.raise_for_status()
        links = response.json()
        return formatted(links, format, "weblinks")
    except HTTPError as e:
        if is_status(e, 404):
            raise HTTPException(status_code=404, detail=f"Issue {key} not found")
        raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/weblink/{key}/{link_id}")
async def remove_weblink(key: str, link_id: str, client=Depends(jira)):
    """Remove web link from issue."""
    try:
        endpoint = f"rest/api/2/issue/{key}/remotelink/{link_id}"
        response = client._session.delete(f"{client.url}/{endpoint}")
        response.raise_for_status()
        return success({"key": key, "link_id": link_id, "removed": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
