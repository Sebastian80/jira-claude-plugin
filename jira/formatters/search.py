"""
Jira Search Results formatters.

Provides Rich, AI, and Markdown formatters for search results.
"""

from typing import Any

from .base import (
    AIFormatter,
    MarkdownFormatter,
    RichFormatter,
    Table,
    Text,
    box,
    get_status_style,
    get_type_icon,
    make_issue_link,
    register_formatter,
    render_to_string,
)

__all__ = ["JiraSearchRichFormatter", "JiraSearchAIFormatter", "JiraSearchMarkdownFormatter"]


@register_formatter("jira", "search", "rich")
class JiraSearchRichFormatter(RichFormatter):
    """Rich terminal search results with tables."""

    def format(self, data: Any) -> str:
        if isinstance(data, list):
            if not data:
                return render_to_string(Text("No issues found", style="yellow"))
            if "fields" in data[0]:
                return self._format_search(data)
        return super().format(data)

    def _format_search(self, issues: list) -> str:
        if not issues:
            return render_to_string(Text("No issues found", style="yellow"))

        table = Table(
            title=f"Search Results ({len(issues)} issues)",
            box=box.ROUNDED,
            header_style="bold",
            border_style="dim",
            title_style="bold",
        )

        # no_wrap=True prevents emoji from wrapping incorrectly
        table.add_column("", width=3, justify="center", no_wrap=True)  # Type icon
        table.add_column("Key", min_width=12, no_wrap=True)  # Clickable links
        table.add_column("Status", min_width=16, no_wrap=True)
        table.add_column("Summary", max_width=40)

        for i in issues:
            f = i.get("fields", {})
            key = i.get("key", "?")
            type_name = f.get("issuetype", {}).get("name", "")
            status_name = f.get("status", {}).get("name", "?")
            summary = f.get("summary", "?")[:40]

            type_icon = get_type_icon(type_name)
            status_icon, status_style = get_status_style(status_name)

            status_text = Text(f"{status_icon} {status_name}", style=status_style)

            table.add_row(type_icon, make_issue_link(key), status_text, summary)

        return render_to_string(table)


@register_formatter("jira", "search", "ai")
class JiraSearchAIFormatter(AIFormatter):
    """AI-optimized search results."""

    def format(self, data: Any) -> str:
        # Handle dict with 'issues' key (from GetIssues bulk fetch)
        if isinstance(data, dict) and "issues" in data:
            return self._format_search_response(data)
        # Handle direct list of issues
        if isinstance(data, list):
            if not data:
                return "NO_ISSUES_FOUND"
            if isinstance(data[0], dict) and "fields" in data[0]:
                return self._format_search(data)
        return super().format(data)

    def _format_search_response(self, response: dict) -> str:
        """Format search response dict with issues and metadata."""
        issues = response.get("issues", [])
        lines = self._format_search(issues).split("\n")

        # Add warning about missing issues if present
        if response.get("missing"):
            lines.append(f"MISSING: {', '.join(response['missing'])}")
        if response.get("_warning"):
            lines.append(f"WARNING: {response['_warning']}")

        return "\n".join(lines)

    def _format_search(self, issues: list) -> str:
        if not issues:
            return "NO_ISSUES_FOUND"
        lines = [f"FOUND: {len(issues)} issues"]
        for i in issues[:30]:
            f = i.get("fields", {})
            status = f.get("status", {}).get("name", "?")
            summary = f.get("summary", "?")[:60]
            lines.append(f"- {i.get('key')}: [{status}] {summary}")
        if len(issues) > 30:
            lines.append(f"... and {len(issues) - 30} more")
        return "\n".join(lines)


@register_formatter("jira", "search", "markdown")
class JiraSearchMarkdownFormatter(MarkdownFormatter):
    """Markdown search results table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list):
            if not data:
                return "*No issues found*"
            if isinstance(data[0], dict) and "fields" in data[0]:
                return self._format_search(data)
        return super().format(data)

    def _format_search(self, issues: list) -> str:
        if not issues:
            return "*No issues found*"
        lines = [
            "| Key | Status | Priority | Summary |",
            "|-----|--------|----------|---------|",
        ]
        for i in issues[:50]:
            f = i.get("fields", {})
            lines.append(
                f"| {i.get('key')} | {f.get('status', {}).get('name', '?')} | "
                f"{f.get('priority', {}).get('name', '?')} | {f.get('summary', '?')[:40]} |"
            )
        return "\n".join(lines)
