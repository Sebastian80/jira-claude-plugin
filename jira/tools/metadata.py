"""
Metadata tools - Reference data operations.

Tools:
- GetPriorities: List all priority levels
- GetStatuses: List all statuses
- GetStatus: Get status by name
- GetFields: List all fields
- GetFilters: List favorite filters
- GetFilter: Get filter details
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetPriorities", "GetStatuses", "GetStatus", "GetFields", "GetFilters", "GetFilter"]

# English to common localized name mappings (for JQL compatibility)
STATUS_ALIASES = {
    "open": ["offen"],
    "closed": ["geschlossen"],
    "resolved": ["erledigt"],
    "in progress": ["in arbeit"],
    "to do": ["zu erledigen"],
    "done": ["fertig"],
    "new": ["neu"],
    "reopened": ["neueröffnet", "wieder geöffnet"],
}


def normalize_status_name(name: str) -> list[str]:
    """Return list of possible status names to search for."""
    name_lower = name.lower()
    candidates = [name_lower]

    # If English name given, add German aliases
    if name_lower in STATUS_ALIASES:
        candidates.extend(STATUS_ALIASES[name_lower])

    # If German name given, add English equivalent
    for english, aliases in STATUS_ALIASES.items():
        if name_lower in aliases:
            candidates.append(english)
            break

    return candidates


class GetPriorities(Tool):
    """List all priority levels."""

    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/priorities"
        tags = ["metadata"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            priorities = ctx.client.get_all_priorities()
            return formatted(priorities, self.format, "priorities")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class GetStatuses(Tool):
    """List all statuses."""

    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/statuses"
        tags = ["metadata"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            statuses = ctx.client.get_all_statuses()
            return formatted(statuses, self.format, "statuses")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class GetStatus(Tool):
    """Get status by name (accepts English or localized names)."""

    name: str = Field(..., description="Status name (English or localized)")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/status/{name}"
        tags = ["metadata"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            all_statuses = ctx.client.get_all_statuses()
            candidates = normalize_status_name(self.name)

            for status in all_statuses:
                status_name_lower = status.get("name", "").lower()
                if status_name_lower in candidates:
                    return formatted(status, self.format, "status")

            return ToolResult(error=f"Status '{self.name}' not found", status=404)
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class GetFields(Tool):
    """List all fields (optionally only custom fields)."""

    custom_only: bool = Field(False, alias="customOnly", description="List only custom fields")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/fields"
        tags = ["metadata"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            fields = ctx.client.get_all_fields()
            if self.custom_only:
                fields = [f for f in fields if f.get("id", "").startswith("customfield_")]
            return formatted(fields, self.format, "fields")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class GetFilters(Tool):
    """List your favorite filters."""

    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/filters"
        tags = ["metadata"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            endpoint = "rest/api/2/filter/favourite"
            response = ctx.client._session.get(f"{ctx.client.url}/{endpoint}")
            response.raise_for_status()
            filters = response.json()
            return formatted(filters, self.format, "filters")
        except Exception as e:
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                return formatted([], self.format, "filters")
            return ToolResult(error=str(e), status=500)


class GetFilter(Tool):
    """Get filter details."""

    filter_id: str = Field(..., alias="id", description="Filter ID")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/filter/{filter_id}"
        tags = ["metadata"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            filter_data = ctx.client.get_filter(self.filter_id)
            return formatted(filter_data, self.format, "filter")
        except Exception as e:
            return ToolResult(error=str(e), status=500)
