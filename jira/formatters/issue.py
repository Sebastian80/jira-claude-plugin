"""
Jira Issue formatters.

Provides Rich, AI, and Markdown formatters for single issue display.
"""

from typing import Any

from rich.console import Group

from .base import (
    AIFormatter,
    MarkdownFormatter,
    Panel,
    RichFormatter,
    Table,
    Text,
    box,
    get_priority_style,
    get_status_style,
    get_type_icon,
    make_issue_link,
    render_to_string,
)

__all__ = ["JiraIssueRichFormatter", "JiraIssueAIFormatter", "JiraIssueMarkdownFormatter"]


class JiraIssueRichFormatter(RichFormatter):
    """Rich terminal issue formatting with panels and colors."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and ("fields" in data or "key" in data):
            return self._format_issue(data)
        return super().format(data)

    def _format_issue(self, issue: dict) -> str:
        f = issue.get("fields", {}) or {}
        key = issue.get("key", "?")
        type_name = f.get("issuetype", {}).get("name", "?") if f.get("issuetype") else "?"
        status_name = f.get("status", {}).get("name", "?") if f.get("status") else "?"
        priority_name = f.get("priority", {}).get("name", "") if f.get("priority") else ""
        summary = f.get("summary") or "?"

        type_icon = get_type_icon(type_name)
        status_icon, status_style = get_status_style(status_name)
        priority_icon, priority_style = get_priority_style(priority_name)

        # Build content with summary
        parts = []

        # Summary
        parts.append(Text(summary, style="bold"))
        parts.append(Text(""))  # Blank line

        # Metadata grid
        meta = Table(show_header=False, box=None, padding=(0, 2), expand=False)
        meta.add_column("Field", style="bold dim", width=10)
        meta.add_column("Value")

        # Status with icon and color
        status_text = Text(f"{status_icon} {status_name}", style=status_style)
        meta.add_row("Status", status_text)

        # Priority with icon
        if priority_name:
            priority_text = Text(f"{priority_icon} {priority_name}", style=priority_style)
            meta.add_row("Priority", priority_text)

        # Assignee
        if f.get("assignee"):
            meta.add_row("Assignee", Text(f["assignee"].get("displayName", "?"), style="cyan"))

        # Reporter
        if f.get("reporter"):
            meta.add_row("Reporter", Text(f["reporter"].get("displayName", "?"), style="dim"))

        # Labels
        if f.get("labels"):
            meta.add_row("Labels", Text(", ".join(f["labels"][:5]), style="magenta"))

        parts.append(meta)

        # Add description if present
        if f.get("description"):
            parts.append(Text(""))  # Blank line
            parts.append(Text("Description", style="bold dim"))
            desc = f["description"][:500]
            if len(f["description"]) > 500:
                desc += "..."
            parts.append(Text(desc, style="dim"))

        # Create panel with title (clickable issue key via Rich Text)
        title = Text.assemble(
            (f"{type_icon}  ", ""),
            make_issue_link(key),
            (f"  {type_name}", "dim"),
        )

        panel = Panel(
            Group(*parts),
            title=title,
            title_align="left",
            box=box.ROUNDED,
            border_style="cyan",
            padding=(1, 2),
        )

        return render_to_string(panel)


class JiraIssueAIFormatter(AIFormatter):
    """AI-optimized issue formatting (compact, structured).

    Produces token-efficient output suitable for LLM consumption.
    Handles partial field responses (--fields) and expanded data (--expand changelog).

    Output format:
        ISSUE: KEY
        type: Type Name
        status: Status Name
        ...
        changelog_entries: N (if expanded)
    """

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and ("fields" in data or "key" in data):
            return self._format_issue(data)
        return super().format(data)

    def _format_issue(self, issue: dict) -> str:
        f = issue.get("fields", {}) or {}
        lines = [
            f"ISSUE: {issue.get('key')}",
            f"type: {f.get('issuetype', {}).get('name') if f.get('issuetype') else 'None'}",
            f"status: {f.get('status', {}).get('name') if f.get('status') else 'None'}",
            f"priority: {f.get('priority', {}).get('name') if f.get('priority') else 'None'}",
            f"summary: {f.get('summary') or 'None'}",
        ]
        if f.get("assignee"):
            lines.append(f"assignee: {f['assignee'].get('displayName')}")
        if f.get("description"):
            lines.append(f"description: {f['description'][:600]}")

        # Handle expanded changelog
        if issue.get("changelog"):
            changelog = issue["changelog"]
            histories = changelog.get("histories", [])
            if histories:
                lines.append(f"changelog_entries: {len(histories)}")
                # Show last 3 changes
                for h in histories[:3]:
                    author = h.get("author", {}).get("displayName", "?")
                    created = h.get("created", "?")[:10]
                    items = h.get("items", [])
                    changes = ", ".join(f"{i.get('field')}: {i.get('fromString', '')} -> {i.get('toString', '')}" for i in items[:2])
                    lines.append(f"  - {created} {author}: {changes}")

        return "\n".join(lines)


class JiraIssueMarkdownFormatter(MarkdownFormatter):
    """Markdown issue formatting."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and ("fields" in data or "key" in data):
            return self._format_issue(data)
        return super().format(data)

    def _format_issue(self, issue: dict) -> str:
        f = issue.get("fields", {}) or {}
        type_name = f.get("issuetype", {}).get("name", "?") if f.get("issuetype") else "?"
        status_name = f.get("status", {}).get("name", "?") if f.get("status") else "?"
        priority_name = f.get("priority", {}).get("name", "?") if f.get("priority") else "?"
        lines = [
            f"## {issue.get('key')}: {f.get('summary') or '?'}",
            "",
            "| Field | Value |",
            "|-------|-------|",
            f"| Type | {type_name} |",
            f"| Status | {status_name} |",
            f"| Priority | {priority_name} |",
        ]
        if f.get("assignee"):
            lines.append(f"| Assignee | {f['assignee'].get('displayName', '?')} |")
        if f.get("description"):
            lines.extend(["", "### Description", "", f.get("description", "")[:600]])
        return "\n".join(lines)
