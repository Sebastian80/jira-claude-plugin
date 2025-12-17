"""
Jira Web Links formatters.

Provides Rich and AI formatters for issue web links.
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

__all__ = ["JiraWebLinksRichFormatter", "JiraWebLinksAIFormatter"]


class JiraWebLinksRichFormatter(RichFormatter):
    """Rich terminal web links table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and (not data or "object" in data[0] if data else True):
            return self._format_weblinks(data)
        return super().format(data)

    def _format_weblinks(self, links: list) -> str:
        if not links:
            return render_to_string(Text("No web links", style="yellow"))

        table = Table(
            title=f"Web Links ({len(links)})",
            box=box.SIMPLE,
            header_style="bold",
        )

        table.add_column("ID", style="dim", width=8)
        table.add_column("Title", style="cyan", min_width=30)
        table.add_column("URL", max_width=60, overflow="fold")

        for link in links:
            obj = link.get("object", {})
            table.add_row(
                str(link.get("id", "?")),
                obj.get("title", "?"),
                obj.get("url", "?"),
            )

        return render_to_string(table)


class JiraWebLinksAIFormatter(AIFormatter):
    """AI-optimized web links list."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and (not data or "object" in data[0] if data else True):
            return self._format_weblinks(data)
        return super().format(data)

    def _format_weblinks(self, links: list) -> str:
        if not links:
            return "NO_WEBLINKS"
        lines = [f"WEBLINKS: {len(links)}"]
        for link in links:
            obj = link.get("object", {})
            lines.append(f"- {obj.get('title', '?')}: {obj.get('url', '?')}")
        return "\n".join(lines)
