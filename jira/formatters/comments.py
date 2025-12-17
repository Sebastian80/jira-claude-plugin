"""
Jira Comments formatters.

Provides Rich and AI formatters for issue comments.
"""

from typing import Any

from .base import (
    AIFormatter,
    Panel,
    RichFormatter,
    Text,
    box,
    render_to_string,
)

__all__ = ["JiraCommentsRichFormatter", "JiraCommentsAIFormatter"]


class JiraCommentsRichFormatter(RichFormatter):
    """Rich terminal comments with panels."""

    def format(self, data: Any) -> str:
        if isinstance(data, list):
            if not data:
                return render_to_string(Text("No comments", style="yellow"))
            if "author" in data[0]:
                return self._format_comments(data)
        return super().format(data)

    def _format_comments(self, comments: list) -> str:
        if not comments:
            return render_to_string(Text("No comments", style="yellow"))

        output = []
        output.append(render_to_string(Text(f"Comments ({len(comments)})", style="bold")))
        output.append("")

        for c in comments:
            author = c.get("author", {}).get("displayName", "?")
            created = c.get("created", "?")[:10]
            body = c.get("body", "")[:300]
            if len(c.get("body", "")) > 300:
                body += "..."

            # Create mini panel for each comment
            title = Text()
            title.append(author, style="cyan bold")
            title.append(f"  {created}", style="dim")

            panel = Panel(
                body,
                title=title,
                title_align="left",
                box=box.SIMPLE,
                padding=(0, 1),
            )
            output.append(render_to_string(panel))

        return "\n".join(output)


class JiraCommentsAIFormatter(AIFormatter):
    """AI-optimized comments."""

    def format(self, data: Any) -> str:
        if isinstance(data, list):
            if not data:
                return "NO_COMMENTS"
            if "author" in data[0]:
                return self._format_comments(data)
        return super().format(data)

    def _format_comments(self, comments: list) -> str:
        if not comments:
            return "NO_COMMENTS"
        lines = [f"COMMENTS: {len(comments)}"]
        for c in comments[:10]:
            author = c.get("author", {}).get("displayName", "?")
            body = c.get("body", "")[:100].replace("\n", " ")
            lines.append(f"- {author}: {body}")
        return "\n".join(lines)
