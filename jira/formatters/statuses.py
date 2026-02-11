"""
Jira Statuses formatters.

Provides Rich, AI, and Markdown formatters for status lists.
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
    "JiraStatusesRichFormatter",
    "JiraStatusesAIFormatter",
    "JiraStatusesMarkdownFormatter",
]


@register_formatter("jira", "statuses", "rich")
class JiraStatusesRichFormatter(RichFormatter):
    """Rich terminal status table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and data and "statusCategory" in data[0]:
            return self._format_statuses(data)
        return super().format(data)

    def _format_statuses(self, statuses: list) -> str:
        table = Table(
            title="Jira Statuses",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Name", style="bold")
        table.add_column("Category")
        table.add_column("ID", style="dim")

        for s in statuses:
            name = s.get("name", "?")
            category = s.get("statusCategory", {}).get("name", "?")
            status_id = s.get("id", "?")
            table.add_row(name, category, status_id)

        return render_to_string(table)


@register_formatter("jira", "statuses", "ai")
class JiraStatusesAIFormatter(AIFormatter):
    """AI-optimized status list."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and data and "statusCategory" in data[0]:
            return self._format_statuses(data)
        return super().format(data)

    def _format_statuses(self, statuses: list) -> str:
        lines = [f"STATUSES: {len(statuses)}"]

        # Group by category
        categories: dict[str, list] = {}
        for s in statuses:
            cat = s.get("statusCategory", {}).get("name", "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(s.get("name", "?"))

        for cat, names in sorted(categories.items()):
            lines.append(f"\n[{cat}]")
            for name in sorted(names):
                lines.append(f"  - {name}")

        return "\n".join(lines)


@register_formatter("jira", "statuses", "markdown")
class JiraStatusesMarkdownFormatter(MarkdownFormatter):
    """Markdown status table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and data and "statusCategory" in data[0]:
            return self._format_statuses(data)
        return super().format(data)

    def _format_statuses(self, statuses: list) -> str:
        lines = [
            "## Jira Statuses",
            "",
            "| Name | Category | ID |",
            "|------|----------|-----|",
        ]

        for s in statuses:
            name = s.get("name", "?")
            category = s.get("statusCategory", {}).get("name", "?")
            status_id = s.get("id", "?")
            lines.append(f"| {name} | {category} | {status_id} |")

        return "\n".join(lines)
