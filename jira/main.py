"""
Jira CLI Server - Standalone FastAPI application.

No bridge dependency. Self-contained server for Jira operations.

Usage:
    # Start server
    python -m jira.main

    # Or via uvicorn
    uvicorn jira.main:app --host 127.0.0.1 --port 9200
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .deps import init_client, is_healthy, get_error, reset
from .routes import create_router

# Routes that require a path parameter - used for helpful 404 messages
ROUTES_REQUIRING_KEY = {
    "/jira/watchers": "watchers/{key} - List watchers for an issue",
    "/jira/watcher": "watcher/{key} - Add watcher (POST) or remove (DELETE)",
    "/jira/comments": "comments/{key} - List comments for an issue",
    "/jira/comment": "comment/{key} - Add comment (POST) or delete (DELETE comment/{key}/{id})",
    "/jira/attachments": "attachments/{key} - List attachments for an issue",
    "/jira/attachment": "attachment/{key} - Upload attachment (POST) or delete (DELETE)",
    "/jira/links": "links/{key} - List links for an issue",
    "/jira/transitions": "transitions/{key} - List available transitions for an issue",
    "/jira/transition": "transition/{key} - Transition issue to new status (POST)",
    "/jira/worklogs": "worklogs/{key} - List worklogs for an issue",
    "/jira/worklog": "worklog/{key} - Add worklog (POST) or get by ID",
    "/jira/weblinks": "weblinks/{key} - List web links for an issue",
    "/jira/weblink": "weblink/{key} - Add web link (POST) or delete",
    "/jira/issue": "issue/{key} - Get issue details",
    "/jira/project": "project/{key} - Get project details",
    "/jira/status": "status/{name} - Get status by name",
}

# Configure logging
logging.basicConfig(
    level=os.environ.get("JIRA_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("jira")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize client on startup."""
    logger.info("Jira CLI server starting...")
    try:
        init_client()
        logger.info("Jira client connected")
    except Exception as e:
        logger.warning(f"Jira client connection failed: {e}")
        # Don't fail startup - allow health checks to report status

    yield

    logger.info("Jira CLI server shutting down...")
    reset()


# Create FastAPI app
app = FastAPI(
    title="Jira CLI API",
    description="Standalone Jira CLI server for Claude Code",
    version="2.0.0",
    lifespan=lifespan,
)


# Health endpoint at root level
@app.get("/health")
async def health():
    """Health check endpoint."""
    healthy = is_healthy()
    err = get_error()

    if healthy:
        return {"status": "healthy", "service": "jira"}
    else:
        return {
            "status": "unhealthy",
            "service": "jira",
            "error": err,
        }


@app.get("/")
async def root():
    """Root endpoint - show basic info."""
    return PlainTextResponse(
        "Jira CLI Server v2.0.0\n"
        "Use /jira/help for available commands\n"
        "Use /health for status\n"
    )


# Mount router with all Jira endpoints
app.include_router(create_router(), prefix="/jira", tags=["jira"])


# Custom 404 handler with helpful error messages
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Provide helpful error messages for 404 errors."""
    if exc.status_code == 404:
        path = request.url.path

        # Check if this is a route that requires a parameter
        for route_prefix, hint in ROUTES_REQUIRING_KEY.items():
            if path == route_prefix or path == route_prefix + "/":
                return JSONResponse(
                    status_code=404,
                    content={
                        "detail": f"Missing required parameter. Usage: {hint}",
                        "hint": "Provide the issue key or required parameter",
                    },
                )

        # Generic 404
        return JSONResponse(
            status_code=404,
            content={"detail": "Endpoint not found. Use /jira/help to see available commands."},
        )

    # For other HTTP exceptions, return standard response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


def main():
    """Run the server."""
    import uvicorn

    host = os.environ.get("JIRA_HOST", "127.0.0.1")
    port = int(os.environ.get("JIRA_PORT", "9200"))

    logger.info(f"Starting Jira CLI server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",  # Reduce uvicorn noise
    )


if __name__ == "__main__":
    main()
