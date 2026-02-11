"""
Jira User formatters.

Provides Rich, AI, and Markdown formatters for user data.
"""

from typing import Any

from .base import (
    AIFormatter,
    MarkdownFormatter,
    Panel,
    RichFormatter,
    Table,
    Text,
    box,
    register_formatter,
    render_to_string,
)

__all__ = ["JiraUserRichFormatter", "JiraUserAIFormatter", "JiraUserMarkdownFormatter"]


def _is_user_data(data: dict) -> bool:
    """Check if data looks like a Jira user response.

    Args:
        data: Dictionary to check

    Returns:
        True if data appears to be a Jira user (has key/name/emailAddress fields)
    """
    # User responses have specific fields
    if "emailAddress" in data or "displayName" in data:
        return True
    # Also check for user-like structure (has name but not fields which would be an issue)
    if "name" in data and "fields" not in data and "key" in data:
        # Could be user if key doesn't look like issue key
        key = data.get("key", "")
        if not (isinstance(key, str) and "-" in key and key.split("-")[-1].isdigit()):
            return True
    return False


@register_formatter("jira", "user", "rich")
class JiraUserRichFormatter(RichFormatter):
    """Rich terminal user formatting with panels and colors."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and _is_user_data(data):
            return self._format_user(data)
        return super().format(data)

    def _format_user(self, user: dict) -> str:
        display_name = user.get("displayName", user.get("name", "?"))
        username = user.get("name", user.get("key", "?"))
        email = user.get("emailAddress", "")
        active = user.get("active", True)
        timezone = user.get("timeZone", "")
        locale = user.get("locale", "")

        # Build content
        parts = []

        # Status indicator
        status = Text("● Active", style="green") if active else Text("○ Inactive", style="red")
        parts.append(status)
        parts.append(Text(""))

        # User details table
        meta = Table(show_header=False, box=None, padding=(0, 2), expand=False)
        meta.add_column("Field", style="bold dim", width=12)
        meta.add_column("Value")

        meta.add_row("Username", Text(username, style="cyan"))
        if email:
            meta.add_row("Email", Text(email, style="blue"))
        if timezone:
            meta.add_row("Timezone", Text(timezone, style="dim"))
        if locale:
            meta.add_row("Locale", Text(locale, style="dim"))

        parts.append(meta)

        # Create panel
        panel = Panel(
            "\n".join(str(p) if isinstance(p, Text) else render_to_string(p) for p in parts),
            title=Text(f"👤 {display_name}", style="bold"),
            title_align="left",
            box=box.ROUNDED,
            border_style="cyan",
            padding=(1, 2),
        )

        return render_to_string(panel)


@register_formatter("jira", "user", "ai")
class JiraUserAIFormatter(AIFormatter):
    """AI-optimized user formatting (compact, structured).

    Output format:
        USER: username
        name: Display Name
        email: user@example.com
        active: true
        timezone: Europe/Berlin
    """

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and _is_user_data(data):
            return self._format_user(data)
        return super().format(data)

    def _format_user(self, user: dict) -> str:
        lines = [
            f"USER: {user.get('name', user.get('key', '?'))}",
            f"name: {user.get('displayName', 'None')}",
            f"email: {user.get('emailAddress', 'None')}",
            f"active: {str(user.get('active', True)).lower()}",
        ]
        if user.get("timeZone"):
            lines.append(f"timezone: {user['timeZone']}")
        if user.get("locale"):
            lines.append(f"locale: {user['locale']}")
        return "\n".join(lines)


@register_formatter("jira", "user", "markdown")
class JiraUserMarkdownFormatter(MarkdownFormatter):
    """Markdown user formatting."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and _is_user_data(data):
            return self._format_user(data)
        return super().format(data)

    def _format_user(self, user: dict) -> str:
        display_name = user.get("displayName", user.get("name", "?"))
        lines = [
            f"## User: {display_name}",
            "",
            "| Field | Value |",
            "|-------|-------|",
            f"| Username | {user.get('name', user.get('key', '?'))} |",
            f"| Email | {user.get('emailAddress', '-')} |",
            f"| Active | {'Yes' if user.get('active', True) else 'No'} |",
        ]
        if user.get("timeZone"):
            lines.append(f"| Timezone | {user['timeZone']} |")
        if user.get("locale"):
            lines.append(f"| Locale | {user['locale']} |")
        return "\n".join(lines)
