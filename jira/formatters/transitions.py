"""
Jira Transitions formatters.

Provides Rich and AI formatters for workflow transitions.
"""

from typing import Any

from .base import (
    AIFormatter,
    RichFormatter,
    Table,
    Text,
    box,
    get_status_style,
    render_to_string,
)

__all__ = ["JiraTransitionsRichFormatter", "JiraTransitionsAIFormatter"]


class JiraTransitionsRichFormatter(RichFormatter):
    """Rich terminal transitions table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list):
            if not data:
                return render_to_string(Text("No transitions available", style="yellow"))
            if "to" in data[0]:
                return self._format_transitions(data)
        return super().format(data)

    def _format_transitions(self, transitions: list) -> str:
        if not transitions:
            return render_to_string(Text("No transitions available", style="yellow"))

        table = Table(
            title="Available Transitions",
            box=box.SIMPLE,
            header_style="bold",
            title_style="bold",
        )

        table.add_column("Action", style="cyan", min_width=25)
        table.add_column("→", justify="center", width=3)
        table.add_column("Target Status", min_width=20)

        for t in transitions:
            name = t.get("name", "?")
            to_status = t.get("to", "?")
            status_icon, status_style = get_status_style(to_status)
            status_text = Text(f"{status_icon} {to_status}", style=status_style)

            table.add_row(name, "→", status_text)

        return render_to_string(table)


class JiraTransitionsAIFormatter(AIFormatter):
    """AI-optimized transitions."""

    def format(self, data: Any) -> str:
        if isinstance(data, list):
            if not data:
                return "NO_TRANSITIONS_AVAILABLE"
            if "to" in data[0]:
                return self._format_transitions(data)
        return super().format(data)

    def _format_transitions(self, transitions: list) -> str:
        if not transitions:
            return "NO_TRANSITIONS_AVAILABLE"
        lines = ["AVAILABLE_TRANSITIONS:"]
        for t in transitions:
            lines.append(f"- {t.get('name')} (id:{t.get('id')}) -> {t.get('to')}")
        return "\n".join(lines)
