"""
Jira Projects formatters.

Provides Rich, AI, and Markdown formatters for project lists and single projects.
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
    "JiraProjectsRichFormatter",
    "JiraProjectsAIFormatter",
    "JiraProjectsMarkdownFormatter",
    "JiraProjectRichFormatter",
    "JiraProjectAIFormatter",
    "JiraProjectMarkdownFormatter",
]


def _project_key_name(p: dict) -> tuple[str, str]:
    return p.get("key", "?"), p.get("name", "?")


# --- Projects list formatters ---


@register_formatter("jira", "projects", "rich")
class JiraProjectsRichFormatter(RichFormatter):
    """Rich terminal project table."""

    def format(self, data: Any) -> str:
        if not isinstance(data, list):
            return super().format(data)
        table = Table(
            title="Jira Projects",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Key", style="bold")
        table.add_column("Name")
        table.add_column("Type", style="dim")

        for p in data:
            key, name = _project_key_name(p)
            ptype = p.get("projectTypeKey", "")
            table.add_row(key, name, ptype)

        return render_to_string(table)


@register_formatter("jira", "projects", "ai")
class JiraProjectsAIFormatter(AIFormatter):
    """AI-optimized project list."""

    def format(self, data: Any) -> str:
        if not isinstance(data, list):
            return super().format(data)
        lines = [f"PROJECTS: {len(data)}"]
        for p in data:
            key, name = _project_key_name(p)
            lines.append(f"  - {key}: {name}")
        return "\n".join(lines)


@register_formatter("jira", "projects", "markdown")
class JiraProjectsMarkdownFormatter(MarkdownFormatter):
    """Markdown project table."""

    def format(self, data: Any) -> str:
        if not isinstance(data, list):
            return super().format(data)
        lines = [
            "## Jira Projects",
            "",
            "| Key | Name | Type |",
            "|-----|------|------|",
        ]
        for p in data:
            key, name = _project_key_name(p)
            ptype = p.get("projectTypeKey", "")
            lines.append(f"| {key} | {name} | {ptype} |")
        return "\n".join(lines)


# --- Single project formatters ---


@register_formatter("jira", "project", "rich")
class JiraProjectRichFormatter(RichFormatter):
    """Rich terminal single project view."""

    def format(self, data: Any) -> str:
        if not isinstance(data, dict) or "key" not in data:
            return super().format(data)
        key, name = _project_key_name(data)
        lead = data.get("lead", {}).get("displayName", "Unknown")
        ptype = data.get("projectTypeKey", "")
        desc = data.get("description", "") or ""

        content = Text()
        content.append(f"{name}\n", style="bold")
        content.append(f"Lead: {lead}\n", style="dim")
        content.append(f"Type: {ptype}\n", style="dim")
        if desc:
            content.append(f"\n{desc}")

        from .base import Panel
        panel = Panel(content, title=f"[bold cyan]{key}[/]", box=box.ROUNDED)
        return render_to_string(panel)


@register_formatter("jira", "project", "ai")
class JiraProjectAIFormatter(AIFormatter):
    """AI-optimized single project."""

    def format(self, data: Any) -> str:
        if not isinstance(data, dict) or "key" not in data:
            return super().format(data)
        key, name = _project_key_name(data)
        lead = data.get("lead", {}).get("displayName", "Unknown")
        ptype = data.get("projectTypeKey", "")
        desc = data.get("description", "") or ""
        lines = [
            f"PROJECT: {key}",
            f"name: {name}",
            f"lead: {lead}",
            f"type: {ptype}",
        ]
        if desc:
            lines.append(f"description: {desc}")
        return "\n".join(lines)


@register_formatter("jira", "project", "markdown")
class JiraProjectMarkdownFormatter(MarkdownFormatter):
    """Markdown single project view."""

    def format(self, data: Any) -> str:
        if not isinstance(data, dict) or "key" not in data:
            return super().format(data)
        key, name = _project_key_name(data)
        lead = data.get("lead", {}).get("displayName", "Unknown")
        ptype = data.get("projectTypeKey", "")
        desc = data.get("description", "") or ""
        lines = [
            f"## {key}: {name}",
            "",
            "| Field | Value |",
            "|-------|-------|",
            f"| Lead | {lead} |",
            f"| Type | {ptype} |",
        ]
        if desc:
            lines.extend(["", "### Description", "", desc])
        return "\n".join(lines)
