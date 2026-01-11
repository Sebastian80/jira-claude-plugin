"""
Combined Issue + Comments formatter.

Shows issue details and comments in a single unified view.
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
    convert_jira_markup,
    get_priority_style,
    get_status_style,
    get_type_icon,
    make_issue_link,
    render_to_string,
)

__all__ = ["JiraShowRichFormatter", "JiraShowAIFormatter", "JiraShowMarkdownFormatter"]


class JiraShowRichFormatter(RichFormatter):
    """Rich combined issue + comments view."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and "issue" in data and "comments" in data:
            return self._format_combined(data)
        return super().format(data)

    def _format_combined(self, data: dict) -> str:
        issue = data.get("issue", {})
        comments = data.get("comments", [])

        f = issue.get("fields", {}) or {}
        key = issue.get("key", "?")
        type_name = f.get("issuetype", {}).get("name", "?") if f.get("issuetype") else "?"
        status_name = f.get("status", {}).get("name", "?") if f.get("status") else "?"
        priority_name = f.get("priority", {}).get("name", "") if f.get("priority") else ""
        summary = f.get("summary") or "?"

        type_icon = get_type_icon(type_name)
        status_icon, status_style = get_status_style(status_name)
        priority_icon, priority_style = get_priority_style(priority_name)

        parts = []

        # Summary
        parts.append(Text(summary, style="bold"))
        parts.append(Text(""))

        # Metadata
        meta = Table(show_header=False, box=None, padding=(0, 2), expand=False)
        meta.add_column("Field", style="bold dim", width=10)
        meta.add_column("Value")

        status_text = Text(f"{status_icon} {status_name}", style=status_style)
        meta.add_row("Status", status_text)

        if priority_name:
            priority_text = Text(f"{priority_icon} {priority_name}", style=priority_style)
            meta.add_row("Priority", priority_text)

        if f.get("assignee"):
            meta.add_row("Assignee", Text(f["assignee"].get("displayName", "?"), style="cyan"))

        if f.get("reporter"):
            meta.add_row("Reporter", Text(f["reporter"].get("displayName", "?"), style="dim"))

        parts.append(meta)

        # Description
        if f.get("description"):
            parts.append(Text(""))
            parts.append(Text("Description", style="bold underline"))
            desc = f["description"][:1200]
            if len(f["description"]) > 1200:
                desc += "..."
            parts.append(convert_jira_markup(desc))

        # Comments section
        if comments:
            parts.append(Text(""))
            parts.append(Text(f"Comments ({len(comments)})", style="bold underline"))
            parts.append(Text(""))

            for i, c in enumerate(comments):
                author = c.get("author", {}).get("displayName", "?")
                created = c.get("created", "?")[:10]
                body = c.get("body", "")[:400]
                if len(c.get("body", "")) > 400:
                    body += "..."

                # Separator line between comments (not before first)
                if i > 0:
                    parts.append(Text("  " + "─" * 50, style="dim"))
                    parts.append(Text(""))

                # Comment header
                comment_header = Text()
                comment_header.append(f"  {author}", style="cyan bold")
                comment_header.append(f"  ({created})", style="dim")
                parts.append(comment_header)

                # Comment body with markup conversion
                formatted_body = convert_jira_markup(body)
                # Indent the body
                parts.append(Text("  ", style="dim") + formatted_body)
                parts.append(Text(""))
        else:
            parts.append(Text(""))
            parts.append(Text("No comments", style="dim italic"))

        # Create panel
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


class JiraShowAIFormatter(AIFormatter):
    """AI-optimized combined view."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and "issue" in data and "comments" in data:
            return self._format_combined(data)
        return super().format(data)

    def _format_combined(self, data: dict) -> str:
        issue = data.get("issue", {})
        comments = data.get("comments", [])
        f = issue.get("fields", {}) or {}

        lines = [
            f"ISSUE: {issue.get('key')}",
            f"type: {f.get('issuetype', {}).get('name', 'None') if f.get('issuetype') else 'None'}",
            f"status: {f.get('status', {}).get('name', 'None') if f.get('status') else 'None'}",
            f"priority: {f.get('priority', {}).get('name', 'None') if f.get('priority') else 'None'}",
            f"summary: {f.get('summary') or 'None'}",
        ]

        if f.get("assignee"):
            lines.append(f"assignee: {f['assignee'].get('displayName', '?')}")

        if f.get("description"):
            lines.append(f"description: {f['description'][:800]}")

        lines.append(f"comments: {len(comments)}")
        for c in comments[:5]:
            author = c.get("author", {}).get("displayName", "?")
            body = c.get("body", "")[:150].replace("\n", " ")
            lines.append(f"  - {author}: {body}")

        return "\n".join(lines)


class JiraShowMarkdownFormatter(MarkdownFormatter):
    """Markdown combined view."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and "issue" in data and "comments" in data:
            return self._format_combined(data)
        return super().format(data)

    def _format_combined(self, data: dict) -> str:
        issue = data.get("issue", {})
        comments = data.get("comments", [])
        f = issue.get("fields", {}) or {}

        lines = [
            f"## {issue.get('key')}: {f.get('summary') or '?'}",
            "",
            "| Field | Value |",
            "|-------|-------|",
            f"| Type | {f.get('issuetype', {}).get('name', '?') if f.get('issuetype') else '?'} |",
            f"| Status | {f.get('status', {}).get('name', '?') if f.get('status') else '?'} |",
            f"| Priority | {f.get('priority', {}).get('name', '?') if f.get('priority') else '?'} |",
        ]

        if f.get("assignee"):
            lines.append(f"| Assignee | {f['assignee'].get('displayName', '?')} |")

        if f.get("description"):
            lines.extend(["", "### Description", "", f.get("description", "")[:800]])

        lines.extend(["", f"### Comments ({len(comments)})", ""])

        for c in comments:
            author = c.get("author", {}).get("displayName", "?")
            created = c.get("created", "?")[:10]
            body = c.get("body", "")

            lines.append(f"**{author}** ({created})")
            lines.append("")
            lines.append(body)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
