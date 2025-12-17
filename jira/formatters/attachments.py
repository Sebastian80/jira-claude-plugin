"""
Jira Attachments formatters.

Provides Rich and AI formatters for issue attachments.
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

__all__ = ["JiraAttachmentsRichFormatter", "JiraAttachmentsAIFormatter"]


class JiraAttachmentsRichFormatter(RichFormatter):
    """Rich terminal attachments table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and (not data or "filename" in data[0] if data else True):
            return self._format_attachments(data)
        return super().format(data)

    def _format_attachments(self, attachments: list) -> str:
        if not attachments:
            return render_to_string(Text("No attachments", style="yellow"))

        table = Table(
            title=f"Attachments ({len(attachments)})",
            box=box.SIMPLE,
            header_style="bold",
        )

        table.add_column("ID", style="dim", width=8)
        table.add_column("Filename", style="cyan", min_width=25)
        table.add_column("Size", justify="right", width=10)
        table.add_column("Author", min_width=15)

        for a in attachments:
            size = a.get("size", 0)
            if size > 1024 * 1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"

            table.add_row(
                str(a.get("id", "?")),
                a.get("filename", "?"),
                size_str,
                a.get("author", {}).get("displayName", "?"),
            )

        return render_to_string(table)


class JiraAttachmentsAIFormatter(AIFormatter):
    """AI-optimized attachments list."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and (not data or "filename" in data[0] if data else True):
            return self._format_attachments(data)
        return super().format(data)

    def _format_attachments(self, attachments: list) -> str:
        if not attachments:
            return "NO_ATTACHMENTS"
        lines = [f"ATTACHMENTS: {len(attachments)}"]
        for a in attachments:
            lines.append(f"- {a.get('filename', '?')} (id:{a.get('id')}, {a.get('size', 0)} bytes)")
        return "\n".join(lines)
