"""
Jira Boards formatters.

Provides Rich, AI, and Markdown formatters for board lists.
"""

from typing import Any

from .base import (
    AIFormatter,
    MarkdownFormatter,
    RichFormatter,
    Table,
    box,
    register_formatter,
    render_to_string,
)

__all__ = [
    "JiraBoardsRichFormatter",
    "JiraBoardsAIFormatter",
    "JiraBoardsMarkdownFormatter",
]


@register_formatter("jira", "boards", "rich")
class JiraBoardsRichFormatter(RichFormatter):
    """Rich terminal board table."""

    def format(self, data: Any) -> str:
        if not isinstance(data, list):
            return super().format(data)
        table = Table(
            title="Jira Boards",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Type")

        for b in data:
            table.add_row(
                str(b.get("id", "?")),
                b.get("name", "?"),
                b.get("type", "?"),
            )

        return render_to_string(table)


@register_formatter("jira", "boards", "ai")
class JiraBoardsAIFormatter(AIFormatter):
    """AI-optimized board list."""

    def format(self, data: Any) -> str:
        if not isinstance(data, list):
            return super().format(data)
        lines = [f"BOARDS: {len(data)}"]
        for b in data:
            name = b.get("name", "?")
            board_id = b.get("id", "?")
            btype = b.get("type", "?")
            lines.append(f"  - {name} (id:{board_id}, {btype})")
        return "\n".join(lines)


@register_formatter("jira", "boards", "markdown")
class JiraBoardsMarkdownFormatter(MarkdownFormatter):
    """Markdown board table."""

    def format(self, data: Any) -> str:
        if not isinstance(data, list):
            return super().format(data)
        lines = [
            "## Jira Boards",
            "",
            "| ID | Name | Type |",
            "|----|------|------|",
        ]
        for b in data:
            lines.append(
                f"| {b.get('id', '?')} | {b.get('name', '?')} | {b.get('type', '?')} |"
            )
        return "\n".join(lines)
