"""
Jira Health formatters.

Provides Rich, AI, and Markdown formatters for health check data.
"""

from typing import Any

from .base import (
    AIFormatter,
    MarkdownFormatter,
    Panel,
    RichFormatter,
    Text,
    box,
    register_formatter,
    render_to_string,
)

__all__ = ["JiraHealthRichFormatter", "JiraHealthAIFormatter", "JiraHealthMarkdownFormatter"]


def _is_health_data(data: dict) -> bool:
    """Check if data looks like a health check response."""
    return "status" in data and "connected" in data


@register_formatter("jira", "health", "rich")
class JiraHealthRichFormatter(RichFormatter):
    """Rich terminal health formatting."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and _is_health_data(data):
            return self._format_health(data)
        return super().format(data)

    def _format_health(self, health: dict) -> str:
        status = health.get("status", "unknown")
        connected = health.get("connected", False)
        user = health.get("user", "?")
        server = health.get("server", "?")
        error = health.get("error")

        if connected:
            status_text = Text("● Healthy", style="green bold")
            user_text = Text(f"Authenticated as: {user}", style="cyan")
        else:
            status_text = Text("○ Unhealthy", style="red bold")
            user_text = Text(f"Error: {error}", style="red") if error else Text("")

        content = f"{status_text}\n{user_text}\nServer: {server}"

        panel = Panel(
            content,
            title="Jira Connection",
            title_align="left",
            box=box.ROUNDED,
            border_style="green" if connected else "red",
            padding=(1, 2),
        )

        return render_to_string(panel)


@register_formatter("jira", "health", "ai")
class JiraHealthAIFormatter(AIFormatter):
    """AI-optimized health formatting."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and _is_health_data(data):
            return self._format_health(data)
        return super().format(data)

    def _format_health(self, health: dict) -> str:
        lines = [
            f"HEALTH: {health.get('status', 'unknown')}",
            f"connected: {str(health.get('connected', False)).lower()}",
        ]
        if health.get("user"):
            lines.append(f"user: {health['user']}")
        if health.get("server"):
            lines.append(f"server: {health['server']}")
        if health.get("error"):
            lines.append(f"error: {health['error']}")
        return "\n".join(lines)


@register_formatter("jira", "health", "markdown")
class JiraHealthMarkdownFormatter(MarkdownFormatter):
    """Markdown health formatting."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict) and _is_health_data(data):
            return self._format_health(data)
        return super().format(data)

    def _format_health(self, health: dict) -> str:
        status = health.get("status", "unknown")
        connected = health.get("connected", False)
        emoji = "✅" if connected else "❌"

        lines = [
            f"## Jira Health: {emoji} {status.title()}",
            "",
            "| Property | Value |",
            "|----------|-------|",
            f"| Connected | {'Yes' if connected else 'No'} |",
        ]
        if health.get("user"):
            lines.append(f"| User | {health['user']} |")
        if health.get("server"):
            lines.append(f"| Server | {health['server']} |")
        if health.get("error"):
            lines.append(f"| Error | {health['error']} |")
        return "\n".join(lines)
