"""
Unit tests for formatter utility functions in jira/formatters/base.py.

Tests the shared utilities: icon/style lookups, wiki markup conversion,
issue link rendering, and string rendering.
"""

import pytest

from jira.formatters.base import (
    convert_jira_markup,
    get_type_icon,
    get_status_style,
    get_priority_style,
    make_issue_link,
    render_to_string,
    Text,
)


# =============================================================================
# get_type_icon
# =============================================================================


class TestGetTypeIcon:
    """Test issue type to icon mapping."""

    def test_known_type(self):
        assert get_type_icon("Bug") == "🐛"

    def test_case_insensitive(self):
        assert get_type_icon("BUG") == "🐛"
        assert get_type_icon("bug") == "🐛"

    def test_task(self):
        assert get_type_icon("Task") == "☑️"

    def test_story(self):
        assert get_type_icon("Story") == "📗"

    def test_epic(self):
        assert get_type_icon("Epic") == "⚡"

    def test_unknown_type_returns_bullet(self):
        assert get_type_icon("CustomType") == "•"

    def test_empty_string(self):
        assert get_type_icon("") == "•"

    def test_none_returns_bullet(self):
        assert get_type_icon(None) == "•"


# =============================================================================
# get_status_style
# =============================================================================


class TestGetStatusStyle:
    """Test status to (icon, style) mapping."""

    def test_done_status(self):
        icon, style = get_status_style("Done")
        assert icon == "✓"
        assert style == "green"

    def test_in_progress_status(self):
        icon, style = get_status_style("In Progress")
        assert icon == "►"
        assert style == "yellow"

    def test_open_status(self):
        icon, style = get_status_style("Open")
        assert icon == "○"
        assert style == "cyan"

    def test_blocked_status(self):
        icon, style = get_status_style("Blocked")
        assert icon == "✗"
        assert style == "red"

    def test_case_insensitive(self):
        icon, style = get_status_style("DONE")
        assert icon == "✓"

    def test_unknown_status(self):
        icon, style = get_status_style("CustomStatus")
        assert icon == "•"
        assert style == "dim"

    def test_empty_string(self):
        icon, style = get_status_style("")
        assert icon == "?"
        assert style == "dim"

    def test_none(self):
        icon, style = get_status_style(None)
        assert icon == "?"
        assert style == "dim"


# =============================================================================
# get_priority_style
# =============================================================================


class TestGetPriorityStyle:
    """Test priority to (icon, style) mapping."""

    def test_high_priority(self):
        icon, style = get_priority_style("High")
        assert icon == "▲"
        assert style == "yellow"

    def test_critical_priority(self):
        icon, style = get_priority_style("Critical")
        assert icon == "▲▲"
        assert "red" in style

    def test_low_priority(self):
        icon, style = get_priority_style("Low")
        assert icon == "▼"

    def test_unknown_priority(self):
        icon, style = get_priority_style("CustomPriority")
        assert icon == ""
        assert style == "dim"

    def test_empty_string(self):
        icon, style = get_priority_style("")
        assert icon == ""

    def test_none(self):
        icon, style = get_priority_style(None)
        assert icon == ""


# =============================================================================
# make_issue_link
# =============================================================================


class TestMakeIssueLink:
    """Test issue key to Rich Text link creation."""

    def test_returns_text_object(self):
        result = make_issue_link("TEST-123")
        assert isinstance(result, Text)

    def test_contains_key(self):
        result = make_issue_link("TEST-123")
        assert "TEST-123" in result.plain

    def test_with_jira_url_env(self, monkeypatch):
        monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
        # Clear the LRU cache so it picks up the new env var
        from jira.formatters.base import _get_jira_url
        _get_jira_url.cache_clear()
        result = make_issue_link("TEST-123")
        rendered = render_to_string(result)
        assert "TEST-123" in rendered
        # Clean up cache
        _get_jira_url.cache_clear()


# =============================================================================
# render_to_string
# =============================================================================


class TestRenderToString:
    """Test Rich object to string rendering."""

    def test_renders_text(self):
        text = Text("Hello World")
        result = render_to_string(text)
        assert "Hello World" in result

    def test_strips_trailing_whitespace(self):
        text = Text("test")
        result = render_to_string(text)
        assert not result.endswith("\n")


# =============================================================================
# convert_jira_markup
# =============================================================================


class TestConvertJiraMarkup:
    """Test Jira wiki markup to Rich Text conversion."""

    def test_empty_string(self):
        result = convert_jira_markup("")
        assert result.plain == ""

    def test_none_returns_empty(self):
        result = convert_jira_markup(None)
        assert result.plain == ""

    def test_plain_text(self):
        result = convert_jira_markup("Hello world")
        assert "Hello world" in result.plain

    def test_heading(self):
        result = convert_jira_markup("h1. My Heading")
        assert "My Heading" in result.plain

    def test_heading_levels(self):
        for level in range(1, 7):
            result = convert_jira_markup(f"h{level}. Level {level}")
            assert f"Level {level}" in result.plain

    def test_numbered_list(self):
        text = "# First\n# Second\n# Third"
        result = convert_jira_markup(text)
        plain = result.plain
        assert "1." in plain
        assert "2." in plain
        assert "3." in plain
        assert "First" in plain

    def test_bullet_list(self):
        text = "* Item one\n* Item two"
        result = convert_jira_markup(text)
        plain = result.plain
        assert "•" in plain
        assert "Item one" in plain

    def test_bold(self):
        result = convert_jira_markup("This is *bold* text")
        assert "bold" in result.plain

    def test_italic(self):
        result = convert_jira_markup("This is _italic_ text")
        assert "italic" in result.plain

    def test_inline_code(self):
        result = convert_jira_markup("Use {{code}} here")
        assert "code" in result.plain

    def test_link_with_text(self):
        result = convert_jira_markup("[Click here|https://example.com]")
        assert "Click here" in result.plain

    def test_link_without_text(self):
        result = convert_jira_markup("[https://example.com]")
        assert "https://example.com" in result.plain

    def test_code_block_markers_stripped(self):
        text = "{code:java}\nSystem.out.println();\n{code}"
        result = convert_jira_markup(text)
        assert "System.out.println();" in result.plain
        assert "{code" not in result.plain

    def test_multiline_preserves_structure(self):
        text = "Line one\nLine two\nLine three"
        result = convert_jira_markup(text)
        plain = result.plain
        assert "Line one" in plain
        assert "Line two" in plain
        assert "Line three" in plain

    def test_numbered_list_resets_after_non_list(self):
        text = "# First\n# Second\nNot a list\n# One"
        result = convert_jira_markup(text)
        plain = result.plain
        assert "1." in plain
        assert "2." in plain
        # After non-list line, counter resets
        lines = plain.split("\n")
        list_items = [l for l in lines if l.strip().startswith("1.")]
        assert len(list_items) == 2  # Two "1." items (counter resets)
