"""
Jira Issue Links formatters.

Provides Rich and AI formatters for issue links.
"""

from typing import Any

from .base import (
    AIFormatter,
    RichFormatter,
    Table,
    Text,
    box,
    get_status_style,
    make_issue_link,
    render_to_string,
)

__all__ = ["JiraLinksRichFormatter", "JiraLinksAIFormatter"]


class JiraLinksRichFormatter(RichFormatter):
    """Rich terminal issue links table."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and (not data or "type" in data[0]):
            return self._format_links(data)
        return super().format(data)

    def _format_links(self, links: list) -> str:
        if not links:
            return render_to_string(Text("No links found", style="yellow"))

        table = Table(
            title=f"Issue Links ({len(links)})",
            box=box.ROUNDED,
            header_style="bold",
            border_style="dim",
        )

        table.add_column("Relationship", min_width=20)
        table.add_column("Issue", style="cyan", min_width=12)
        table.add_column("Summary", max_width=35)
        table.add_column("Status", min_width=12)

        for link in links:
            link_type = link.get("type", {})

            # Determine direction and get linked issue
            if "outwardIssue" in link:
                direction = link_type.get("outward", "?")
                linked = link.get("outwardIssue", {})
            else:
                direction = link_type.get("inward", "?")
                linked = link.get("inwardIssue", {})

            key = linked.get("key", "?")
            summary = linked.get("fields", {}).get("summary", "?")[:35]
            status = linked.get("fields", {}).get("status", {}).get("name", "?")
            status_icon, status_style = get_status_style(status)

            table.add_row(
                direction,
                make_issue_link(key),
                summary,
                Text(f"{status_icon} {status}", style=status_style),
            )

        return render_to_string(table)


class JiraLinksAIFormatter(AIFormatter):
    """AI-optimized issue links."""

    def format(self, data: Any) -> str:
        if isinstance(data, list) and (not data or "type" in data[0]):
            return self._format_links(data)
        return super().format(data)

    def _format_links(self, links: list) -> str:
        if not links:
            return "NO_LINKS"
        lines = [f"LINKS: {len(links)}"]
        for link in links:
            link_type = link.get("type", {})
            if "outwardIssue" in link:
                direction = link_type.get("outward", "?")
                linked = link.get("outwardIssue", {})
            else:
                direction = link_type.get("inward", "?")
                linked = link.get("inwardIssue", {})
            key = linked.get("key", "?")
            summary = linked.get("fields", {}).get("summary", "?")[:50]
            lines.append(f"- {direction} {key}: {summary}")
        return "\n".join(lines)
