"""
Combined Issue + Comments formatter.

Shows issue details and comments in a single unified view.
Reuses issue formatter helpers for the issue portion.
"""

from typing import Any

from rich.console import Group

from .base import (
    AIFormatter,
    MarkdownFormatter,
    Panel,
    RichFormatter,
    Text,
    box,
    convert_jira_markup,
    render_to_string,
)
from .issue import JiraIssueRichFormatter, JiraIssueAIFormatter, JiraIssueMarkdownFormatter

__all__ = ["JiraShowRichFormatter", "JiraShowAIFormatter", "JiraShowMarkdownFormatter"]

# Shared formatter instances for delegation
_rich_issue = JiraIssueRichFormatter()
_ai_issue = JiraIssueAIFormatter()
_md_issue = JiraIssueMarkdownFormatter()


class JiraShowRichFormatter(RichFormatter):
    """Rich combined issue + comments view."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and "issue" in data and "comments" in data:
            return self._format_combined(data)
        return super().format(data)

    def _format_combined(self, data: dict) -> str:
        issue = data.get("issue", {})
        comments = data.get("comments", [])

        parts, title = _rich_issue._build_issue_parts(
            issue, desc_limit=1200, include_labels=False,
        )

        # Override description heading style for show view
        for i, part in enumerate(parts):
            if isinstance(part, Text) and str(part) == "Description":
                parts[i] = Text("Description", style="bold underline")

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

                if i > 0:
                    parts.append(Text("  " + "─" * 50, style="dim"))
                    parts.append(Text(""))

                comment_header = Text()
                comment_header.append(f"  {author}", style="cyan bold")
                comment_header.append(f"  ({created})", style="dim")
                parts.append(comment_header)

                formatted_body = convert_jira_markup(body)
                parts.append(Text("  ", style="dim") + formatted_body)
                parts.append(Text(""))
        else:
            parts.append(Text(""))
            parts.append(Text("No comments", style="dim italic"))

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

        lines = _ai_issue._build_issue_lines(issue, desc_limit=800)

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

        lines = _md_issue._build_issue_lines(issue, desc_limit=800)

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
