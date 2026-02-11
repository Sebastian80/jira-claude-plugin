"""
Jira Priorities formatters.

Provides Rich, AI, and Markdown formatters for priority lists.
"""

from typing import Any

from .base import (
    AIFormatter,
    MarkdownFormatter,
    RichFormatter,
    Table,
    Text,
    box,
    register_formatter,
    render_to_string,
)

__all__ = [
    "JiraPrioritiesRichFormatter",
    "JiraPrioritiesAIFormatter",
    "JiraPrioritiesMarkdownFormatter",
]


@register_formatter("jira", "priorities", "rich")
class JiraPrioritiesRichFormatter(RichFormatter):
    """Rich terminal priority table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and data and "iconUrl" in data[0]:
            return self._format_priorities(data)
        return super().format(data)

    def _format_priorities(self, priorities: list) -> str:
        table = Table(
            title="Jira Priorities",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Name", style="bold")
        table.add_column("ID", style="dim")

        for p in priorities:
            name = p.get("name", "?")
            priority_id = p.get("id", "?")
            table.add_row(name, priority_id)

        return render_to_string(table)


@register_formatter("jira", "priorities", "ai")
class JiraPrioritiesAIFormatter(AIFormatter):
    """AI-optimized priority list."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and data and "iconUrl" in data[0]:
            return self._format_priorities(data)
        return super().format(data)

    def _format_priorities(self, priorities: list) -> str:
        lines = [f"PRIORITIES: {len(priorities)}"]
        for p in priorities:
            name = p.get("name", "?")
            priority_id = p.get("id", "?")
            lines.append(f"  - {name} (id:{priority_id})")
        return "\n".join(lines)


@register_formatter("jira", "priorities", "markdown")
class JiraPrioritiesMarkdownFormatter(MarkdownFormatter):
    """Markdown priority table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and data and "iconUrl" in data[0]:
            return self._format_priorities(data)
        return super().format(data)

    def _format_priorities(self, priorities: list) -> str:
        lines = [
            "## Jira Priorities",
            "",
            "| Name | ID |",
            "|------|-----|",
        ]

        for p in priorities:
            name = p.get("name", "?")
            priority_id = p.get("id", "?")
            lines.append(f"| {name} | {priority_id} |")

        return "\n".join(lines)
