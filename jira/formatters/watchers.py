"""
Jira Watchers formatters.

Provides Rich and AI formatters for issue watchers.
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

__all__ = ["JiraWatchersRichFormatter", "JiraWatchersAIFormatter"]


class JiraWatchersRichFormatter(RichFormatter):
    """Rich terminal watchers table."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and "watchers" in data:
            return self._format_watchers(data)
        return super().format(data)

    def _format_watchers(self, data: dict) -> str:
        watchers = data.get("watchers", [])
        count = data.get("watchCount", len(watchers))

        if not watchers:
            return render_to_string(Text(f"No watchers (count: {count})", style="yellow"))

        table = Table(
            title=f"Watchers ({count})",
            box=box.SIMPLE,
            header_style="bold",
        )

        table.add_column("Name", style="cyan", min_width=25)
        table.add_column("Username", style="dim", min_width=20)

        for w in watchers:
            table.add_row(
                w.get("displayName", "?"),
                w.get("name", w.get("key", "?")),
            )

        return render_to_string(table)


class JiraWatchersAIFormatter(AIFormatter):
    """AI-optimized watchers list."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and "watchers" in data:
            return self._format_watchers(data)
        return super().format(data)

    def _format_watchers(self, data: dict) -> str:
        watchers = data.get("watchers", [])
        count = data.get("watchCount", len(watchers))
        if not watchers:
            return f"WATCHERS: 0 (count: {count})"
        lines = [f"WATCHERS: {count}"]
        for w in watchers:
            lines.append(f"- {w.get('displayName', '?')} ({w.get('name', '?')})")
        return "\n".join(lines)
