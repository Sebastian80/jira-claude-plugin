"""
Field reference data.

Endpoints:
- GET /fields - List all fields
- GET /fields/custom - List only custom fields
"""

from fastapi import APIRouter, Depends, Query

from ..deps import jira
from ..response import formatted, jira_error_handler

router = APIRouter()


@router.get("/fields")
@jira_error_handler()
async def list_fields(
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List all fields."""
    fields = client.get_all_fields()
    return formatted(fields, format, "fields")


@router.get("/fields/custom")
@jira_error_handler()
async def list_custom_fields(
    format: str = Query("json", description="Output format: json, rich, ai, markdown"),
    client=Depends(jira),
):
    """List only custom fields."""
    all_fields = client.get_all_fields()
    custom_fields = [f for f in all_fields if f.get("id", "").startswith("customfield_")]
    return formatted(custom_fields, format, "custom_fields")
