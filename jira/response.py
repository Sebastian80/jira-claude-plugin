"""
Response formatting utilities.

Handles JSON and text formatting for API responses.
"""

import functools
import inspect
import logging
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from requests import HTTPError

from .formatters import formatter_registry, RichFormatter, AIFormatter, MarkdownFormatter

logger = logging.getLogger("jira.response")


def get_status_code(e: Exception) -> int | None:
    """Extract HTTP status code from an HTTPError, or None for other exceptions."""
    if isinstance(e, HTTPError) and hasattr(e, 'response') and e.response is not None:
        return e.response.status_code
    return None


def is_status(e: Exception, code: int) -> bool:
    """Check if an exception represents a specific HTTP status code."""
    return get_status_code(e) == code

# Valid format values
VALID_FORMATS = {"json", "rich", "ai", "markdown"}

# Default formatters for error messages
_DEFAULT_FORMATTERS = {
    "rich": RichFormatter(),
    "ai": AIFormatter(),
    "markdown": MarkdownFormatter(),
}


def success(data: Any) -> JSONResponse:
    """Standard success response."""
    return JSONResponse(content={"success": True, "data": data})


def error(message: str, hint: str | None = None, status: int = 400) -> JSONResponse:
    """Standard error response."""
    content = {"success": False, "error": message}
    if hint:
        content["hint"] = hint
    return JSONResponse(status_code=status, content=content)


def formatted(data: Any, fmt: str, data_type: str | None = None):
    """Return response in requested format."""
    # Validate format parameter
    if fmt not in VALID_FORMATS:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": f"Invalid format '{fmt}'",
                "hint": f"Valid formats: {', '.join(sorted(VALID_FORMATS))}"
            }
        )

    if fmt == "json":
        return JSONResponse(content={"success": True, "data": data})

    formatter = formatter_registry.get(fmt, plugin="jira", data_type=data_type)
    if formatter is None:
        formatter = formatter_registry.get(fmt)

    if formatter is None:
        return JSONResponse(content={"success": True, "data": data})

    return PlainTextResponse(content=formatter.format(data))


def formatted_error(message: str, hint: str | None = None, fmt: str = "json", status: int = 400):
    """Return error in requested format."""
    if fmt == "json":
        return error(message, hint, status)

    formatter = formatter_registry.get(fmt)
    if formatter is None:
        formatter = _DEFAULT_FORMATTERS.get(fmt)
    if formatter is None:
        return error(message, hint, status)

    return PlainTextResponse(content=formatter.format_error(message, hint), status_code=status)


def jira_error_handler(
    not_found: str | None = None,
    conflict: str | None = None,
    forbidden: str | None = None,
    bad_request: str | None = None,
):
    """Decorator that replaces the standard try/except pattern in route handlers.

    Catches HTTPError and maps status codes to user-friendly error responses.
    Message templates use {name} syntax resolved from the handler's kwargs.
    Automatically detects whether the handler has a `format` parameter and uses
    formatted_error() (format-aware) or error() (plain JSON) accordingly.
    """
    status_map = {}
    if not_found:
        status_map[404] = not_found
    if forbidden:
        status_map[403] = forbidden
    if conflict:
        status_map[409] = conflict
    if bad_request:
        status_map[400] = bad_request

    def decorator(func):
        sig = inspect.signature(func)
        has_format = "format" in sig.parameters

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPError as e:
                status = get_status_code(e)
                template = status_map.get(status)
                if template:
                    # Build context: kwargs + flattened Pydantic body fields
                    ctx = dict(kwargs)
                    for v in kwargs.values():
                        if hasattr(v, "model_dump"):
                            for field, val in v.model_dump().items():
                                ctx.setdefault(field, val)
                    msg = template.format(**ctx)
                    fmt = kwargs.get("format", "json") if has_format else None
                    if has_format:
                        return formatted_error(msg, fmt=fmt, status=status)
                    return error(msg, status=status)
                raise HTTPException(
                    status_code=status or 500, detail=str(e)
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        return wrapper

    return decorator
