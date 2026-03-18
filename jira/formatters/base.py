"""
Base formatter classes and utilities.

Provides base classes, registry, and shared utilities for all Jira formatters.
"""

import functools
import json
import logging
import os
import re
from io import StringIO
from pathlib import Path
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

__all__ = [
    # Base classes
    "Formatter",
    "JsonFormatter",
    "RichFormatter",
    "AIFormatter",
    "MarkdownFormatter",
    # Registry
    "FormatterRegistry",
    "formatter_registry",
    "register_formatter",
    # Utilities
    "render_to_string",
    "make_issue_link",
    "get_type_icon",
    "get_status_style",
    "get_priority_style",
    "convert_jira_markup",
    # Rich re-exports for formatters
    "Table",
    "Panel",
    "Text",
    "box",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Base Formatter Classes
# ═══════════════════════════════════════════════════════════════════════════════


class Formatter:
    """Base formatter with default implementations."""

    def format(self, data: Any) -> str:
        """Format data as string. Override in subclasses."""
        return str(data)

    def format_error(self, message: str, hint: str | None = None) -> str:
        """Format error message."""
        if hint:
            return f"Error: {message}\nHint: {hint}"
        return f"Error: {message}"


class JsonFormatter(Formatter):
    """JSON output formatter."""

    def format(self, data: Any) -> str:
        return json.dumps(data, indent=2, default=str)


class RichFormatter(Formatter):
    """Rich terminal output formatter."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict):
            return json.dumps(data, indent=2, default=str)
        return str(data)


class AIFormatter(Formatter):
    """AI-optimized output formatter (compact, structured)."""

    def format(self, data: Any) -> str:
        return json.dumps(data, separators=(",", ":"), default=str)


class MarkdownFormatter(Formatter):
    """Markdown output formatter."""

    def format(self, data: Any) -> str:
        if isinstance(data, dict):
            return f"```json\n{json.dumps(data, indent=2, default=str)}\n```"
        return str(data)


# ═══════════════════════════════════════════════════════════════════════════════
# Formatter Registry
# ═══════════════════════════════════════════════════════════════════════════════


class FormatterRegistry:
    """Registry for plugin formatters."""

    def __init__(self):
        self._formatters: dict[str, Formatter] = {}

    def register(self, plugin: str, data_type: str, format_name: str, formatter: Formatter):
        """Register a formatter for plugin:data_type:format."""
        key = f"{plugin}:{data_type}:{format_name}"
        self._formatters[key] = formatter

    def get(self, format_name: str, plugin: str | None = None, data_type: str | None = None) -> Formatter | None:
        """Get formatter by format name, optionally filtered by plugin and data_type.

        Args:
            format_name: The format (e.g., "ai", "rich", "markdown")
            plugin: Plugin name (e.g., "jira")
            data_type: Data type (e.g., "issue", "user", "comments")

        Returns:
            Formatter if found, None otherwise.

        Note:
            When data_type is specified, only exact matches are returned.
            We do NOT fall back to other data_types to avoid returning
            wrong formatters (e.g., issue formatter for user data).
        """
        if plugin and data_type:
            key = f"{plugin}:{data_type}:{format_name}"
            return self._formatters.get(key)
        # Only do fallback search if data_type was NOT specified
        if plugin and data_type is None:
            for key, fmt in self._formatters.items():
                if key.startswith(f"{plugin}:") and key.endswith(f":{format_name}"):
                    logger.debug("Formatter fallback: no data_type specified, returning first match '%s'", key)
                    return fmt
        return None


logger = logging.getLogger(__name__)

# Global plugin-local registry
formatter_registry = FormatterRegistry()


def register_formatter(plugin: str, data_type: str, format_name: str):
    """Class decorator that auto-registers a formatter instance with the global registry."""
    def decorator(cls):
        formatter_registry.register(plugin, data_type, format_name, cls())
        return cls
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# Jira URL for Hyperlinks
# ═══════════════════════════════════════════════════════════════════════════════


@functools.lru_cache(maxsize=1)
def _get_jira_url() -> str:
    """Get Jira base URL from environment or config file."""
    from jira.lib.config import load_env
    config = load_env()
    return config.get("JIRA_URL", "").rstrip("/")


def make_issue_link(key: str, jira_url: str = "") -> Text:
    """Create a clickable hyperlink to a Jira issue.

    Returns Rich Text object with native link style.

    Args:
        key: Issue key (e.g., "PROJ-123")
        jira_url: Base Jira URL (auto-detected if empty)
    """
    if not jira_url:
        jira_url = _get_jira_url()

    text = Text(key)
    if jira_url:
        url = f"{jira_url}/browse/{key}"
        text.stylize(f"bold cyan link {url}")
    else:
        text.stylize("bold cyan")
    return text


# ═══════════════════════════════════════════════════════════════════════════════
# Icons & Status Colors
# ═══════════════════════════════════════════════════════════════════════════════


TYPE_ICONS = {
    # Bugs
    "bug": "🐛", "problem": "🐛", "fehler": "🐛", "defect": "🐛",
    # Tasks
    "task": "☑️", "aufgabe": "☑️",
    "technical task": "🔧", "sub: technical task": "🔧",
    # Stories & Features
    "story": "📗", "user story": "📗", "anforderung": "📗", "anforderung / user story": "📗",
    "new feature": "✨", "feature": "✨",
    # Epics
    "epic": "⚡",
    # Sub-tasks
    "subtask": "📎", "sub-task": "📎", "unteraufgabe": "📎",
    # Improvements
    "improvement": "💡", "verbesserung": "💡", "enhancement": "💡",
    # Research & Analysis
    "analyse": "🔬", "analysis": "🔬", "spike": "🔬", "research": "🔬",
    "investigation": "🔍", "sub: investigation": "🔍",
    # Operations
    "deployment": "🚀", "release": "🚀",
    # Training & Docs
    "training-education": "📚", "training": "📚", "documentation": "📝",
    # Support
    "support": "🎧", "question": "❓", "incident": "🚨",
}

STATUS_STYLES = {
    # Done (green)
    "done": ("✓", "green"), "fertig": ("✓", "green"), "closed": ("✓", "green"),
    "geschlossen": ("✓", "green"), "resolved": ("✓", "green"), "released": ("✓", "green"),
    "ready for deployment": ("✓", "green"),
    # In Progress (yellow)
    "in progress": ("►", "yellow"), "in arbeit": ("►", "yellow"),
    "in review": ("►", "yellow"), "in entwicklung": ("►", "yellow"),
    "development": ("►", "yellow"),
    # Waiting (yellow dim)
    "waiting": ("◦", "yellow"), "wartend": ("◦", "yellow"),
    "waiting for qa": ("◦", "yellow"), "awaiting approval": ("◦", "yellow"),
    # Blocked (red)
    "blocked": ("✗", "red"), "blockiert": ("✗", "red"),
    # Open/To Do (cyan)
    "to do": ("○", "cyan"), "zu erledigen": ("○", "cyan"), "open": ("○", "cyan"),
    "offen": ("○", "cyan"), "new": ("○", "cyan"), "neu": ("○", "cyan"),
    "backlog": ("·", "dim"),
    # Review
    "review": ("◎", "yellow"), "code review": ("◎", "yellow"),
    "analyse": ("◎", "cyan"),
}

PRIORITY_STYLES = {
    "blocker": ("▲▲", "bold red"), "critical": ("▲▲", "bold red"),
    "highest": ("▲", "red"), "high": ("▲", "yellow"),
    "medium": ("─", "dim"), "low": ("▼", "dim"), "lowest": ("▼▼", "dim"),
}


def get_type_icon(type_name: str) -> str:
    """Get icon for issue type."""
    if not type_name:
        return "•"
    return TYPE_ICONS.get(type_name.lower(), "•")


def get_status_style(status_name: str) -> tuple[str, str]:
    """Get icon and style for status."""
    if not status_name:
        return ("?", "dim")
    return STATUS_STYLES.get(status_name.lower(), ("•", "dim"))


def get_priority_style(priority_name: str) -> tuple[str, str]:
    """Get icon and style for priority."""
    if not priority_name:
        return ("", "dim")
    return PRIORITY_STYLES.get(priority_name.lower(), ("", "dim"))


def render_to_string(renderable) -> str:
    """Render a Rich object to ANSI string."""
    console = Console(file=StringIO(), force_terminal=True, width=80)
    console.print(renderable)
    return console.file.getvalue().rstrip()


# ═══════════════════════════════════════════════════════════════════════════════
# Jira Wiki Markup Conversion
# ═══════════════════════════════════════════════════════════════════════════════

def convert_jira_markup(text: str) -> Text:
    """Convert Jira wiki markup to Rich Text.

    Handles:
    - h1. h2. h3. etc → Bold headings
    - # numbered lists → 1. 2. 3.
    - * bullet lists → •
    - *bold* → bold
    - _italic_ → italic
    - {{code}} → monospace
    - {code}...{code} → code block
    - [text|url] → link text
    """
    if not text:
        return Text("")

    lines = text.split("\n")
    result = Text()
    list_counter = 0

    for i, line in enumerate(lines):
        if i > 0:
            result.append("\n")

        # Headings: h1. h2. h3. etc
        heading_match = re.match(r"^h([1-6])\.\s*(.*)$", line)
        if heading_match:
            level = int(heading_match.group(1))
            heading_text = heading_match.group(2)
            # Convert inline markup in heading
            result.append(_convert_inline_markup(heading_text, base_style="bold"))
            list_counter = 0
            continue

        # Numbered list: # item
        if line.startswith("# "):
            list_counter += 1
            item_text = line[2:]
            result.append(f"{list_counter}. ", style="cyan")
            result.append(_convert_inline_markup(item_text))
            continue

        # Bullet list: * item (but not **bold**)
        if re.match(r"^\* (?!\*)", line):
            item_text = line[2:]
            result.append("• ", style="cyan")
            result.append(_convert_inline_markup(item_text))
            list_counter = 0
            continue

        # Code block: {code}...{code}
        if line.strip().startswith("{code"):
            # Skip code markers, content will be on next lines
            continue
        if line.strip() == "{code}":
            continue

        # Regular line - convert inline markup
        result.append(_convert_inline_markup(line))
        if not line.startswith("# "):
            list_counter = 0

    return result


def _convert_inline_markup(text: str, base_style: str = "") -> Text:
    """Convert inline Jira markup to Rich Text.

    Args:
        text: Text with Jira markup
        base_style: Base style to apply (e.g., "bold" for headings)
    """
    result = Text()

    # Process the text character by character with regex
    # Pattern order matters - more specific patterns first
    patterns = [
        # {{monospace}}
        (r"\{\{([^}]+)\}\}", "code", "cyan"),
        # *bold* (but not ** which would be empty)
        (r"\*([^*]+)\*", "bold", base_style + " bold" if base_style else "bold"),
        # _italic_
        (r"_([^_]+)_", "italic", base_style + " italic" if base_style else "italic"),
        # -strikethrough-
        (r"-([^-]+)-", "strike", "strike"),
        # [text|url] or [url]
        (r"\[([^|\]]+)(?:\|[^\]]+)?\]", "link", "cyan underline"),
    ]

    # Simple approach: find and replace patterns, building styled text
    remaining = text
    while remaining:
        earliest_match = None
        earliest_pos = len(remaining)
        matched_style = base_style or ""

        for pattern, _, style in patterns:
            match = re.search(pattern, remaining)
            if match and match.start() < earliest_pos:
                earliest_match = match
                earliest_pos = match.start()
                matched_style = style

        if earliest_match:
            # Add text before match
            if earliest_pos > 0:
                result.append(remaining[:earliest_pos], style=base_style or None)
            # Add matched text with style
            result.append(earliest_match.group(1), style=matched_style)
            remaining = remaining[earliest_match.end():]
        else:
            # No more matches, add remaining text
            result.append(remaining, style=base_style or None)
            break

    return result
