"""
Jira Worklogs formatters.

Provides Rich and AI formatters for issue worklogs (time tracking).
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

__all__ = ["JiraWorklogsRichFormatter", "JiraWorklogsAIFormatter"]


class JiraWorklogsRichFormatter(RichFormatter):
    """Rich terminal worklogs table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and (not data or "timeSpent" in data[0]):
            return self._format_worklogs(data)
        return super().format(data)

    def _format_worklogs(self, worklogs: list) -> str:
        if not worklogs:
            return render_to_string(Text("No worklogs", style="yellow"))

        table = Table(
            title=f"Worklogs ({len(worklogs)})",
            box=box.SIMPLE,
            header_style="bold",
        )

        table.add_column("ID", style="dim", width=8)
        table.add_column("Author", style="cyan", min_width=20)
        table.add_column("Time", min_width=10)
        table.add_column("Date", min_width=12)
        table.add_column("Comment", max_width=30)

        for w in worklogs:
            table.add_row(
                str(w.get("id", "?")),
                w.get("author", {}).get("displayName", "?"),
                w.get("timeSpent", "?"),
                w.get("started", "?")[:10],
                (w.get("comment", "") or "")[:30],
            )

        return render_to_string(table)


class JiraWorklogsAIFormatter(AIFormatter):
    """AI-optimized worklogs list."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and (not data or "timeSpent" in data[0]):
            return self._format_worklogs(data)
        return super().format(data)

    def _format_worklogs(self, worklogs: list) -> str:
        if not worklogs:
            return "NO_WORKLOGS"
        lines = [f"WORKLOGS: {len(worklogs)}"]
        for w in worklogs:
            author = w.get("author", {}).get("displayName", "?")
            time = w.get("timeSpent", "?")
            date = w.get("started", "?")[:10]
            lines.append(f"- {author}: {time} on {date}")
        return "\n".join(lines)
