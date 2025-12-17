"""
Jira Link Types formatters.

Provides Rich and AI formatters for available link types.
"""

from typing import Any

from .base import (
    AIFormatter,
    RichFormatter,
    Table,
    Text,
    box,
    render_to_string,
)

__all__ = ["JiraLinkTypesRichFormatter", "JiraLinkTypesAIFormatter"]


class JiraLinkTypesRichFormatter(RichFormatter):
    """Rich terminal link types table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and data and "inward" in data[0]:
            return self._format_linktypes(data)
        return super().format(data)

    def _format_linktypes(self, types: list) -> str:
        if not types:
            return render_to_string(Text("No link types found", style="yellow"))

        table = Table(
            title=f"Link Types ({len(types)})",
            box=box.ROUNDED,
            header_style="bold",
            border_style="dim",
        )

        table.add_column("Name", style="cyan bold", min_width=15)
        table.add_column("Outward", min_width=20)
        table.add_column("Inward", min_width=20)

        for lt in types:
            table.add_row(
                lt.get("name", "?"),
                lt.get("outward", "?"),
                lt.get("inward", "?"),
            )

        return render_to_string(table)


class JiraLinkTypesAIFormatter(AIFormatter):
    """AI-optimized link types."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and data and "inward" in data[0]:
            return self._format_linktypes(data)
        return super().format(data)

    def _format_linktypes(self, types: list) -> str:
        if not types:
            return "NO_LINK_TYPES"
        lines = [f"LINK_TYPES: {len(types)}"]
        for lt in types:
            lines.append(f"- {lt.get('name')}: {lt.get('outward')} / {lt.get('inward')}")
        return "\n".join(lines)
