"""
Combined router for all Jira endpoints.

Uses the tools framework for tool classes, plus manual routes for help.
"""

from fastapi import APIRouter, Depends

from toolbus.tools import register_tools

from ..deps import jira
from ..response import formatted
from ..tools import ALL_TOOLS
from .help import router as help_router


def create_router() -> APIRouter:
    """Create and return the combined router with all endpoints."""
    router = APIRouter()

    # Help endpoint (reads OpenAPI at runtime, kept as manual route)
    router.include_router(help_router)

    # Register all tools with auto-generated routes
    register_tools(
        router,
        ALL_TOOLS,
        client_dependency=Depends(jira),
        formatter=formatted,
    )

    return router
