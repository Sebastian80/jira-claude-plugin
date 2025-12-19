"""
Tests for Jira-specific formatters.
"""

import sys
from pathlib import Path

import pytest

# Setup paths - add jira package root to path
PLUGIN_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from jira.formatters import (
    JiraIssueRichFormatter,
    JiraIssueAIFormatter,
    JiraIssueMarkdownFormatter,
    JiraSearchRichFormatter,
    JiraSearchAIFormatter,
    JiraSearchMarkdownFormatter,
    JiraTransitionsRichFormatter,
    JiraTransitionsAIFormatter,
    JiraCommentsRichFormatter,
    JiraCommentsAIFormatter,
    register_jira_formatters,
    formatter_registry,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Issue Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraIssueRichFormatter:
    """Tests for rich issue formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraIssueRichFormatter()

    def test_format_issue_basic(self, formatter, sample_issue):
        """Should format issue with key, type, status, priority."""
        result = formatter.format(sample_issue)

        assert "TEST-123" in result
        assert "Story" in result
        assert "In Progress" in result
        assert "High" in result

    def test_format_issue_includes_summary(self, formatter, sample_issue):
        """Should include issue summary."""
        result = formatter.format(sample_issue)
        assert "Sample test issue summary" in result

    def test_format_issue_includes_assignee(self, formatter, sample_issue):
        """Should include assignee name."""
        result = formatter.format(sample_issue)
        assert "John Doe" in result

    def test_format_issue_includes_description(self, formatter, sample_issue):
        """Should include truncated description."""
        result = formatter.format(sample_issue)
        assert "detailed description" in result

    def test_format_issue_without_assignee(self, formatter):
        """Should handle missing assignee."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "summary": "No assignee",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Low"},
            }
        }
        result = formatter.format(issue)
        assert "TEST-1" in result
        assert "Assignee" not in result

    def test_format_non_issue_data(self, formatter):
        """Should fall back to base formatter for non-issue data."""
        result = formatter.format({"key": "value"})
        assert "key" in result.lower()


class TestJiraIssueAIFormatter:
    """Tests for AI-optimized issue formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraIssueAIFormatter()

    def test_format_issue_concise(self, formatter, sample_issue):
        """Should produce concise output for AI consumption."""
        result = formatter.format(sample_issue)

        assert "ISSUE: TEST-123" in result
        assert "type: Story" in result
        assert "status: In Progress" in result
        assert "priority: High" in result

    def test_format_issue_includes_summary(self, formatter, sample_issue):
        """Should include summary."""
        result = formatter.format(sample_issue)
        assert "summary:" in result.lower()

    def test_format_issue_includes_assignee(self, formatter, sample_issue):
        """Should include assignee."""
        result = formatter.format(sample_issue)
        assert "assignee:" in result.lower()


class TestJiraIssueMarkdownFormatter:
    """Tests for markdown issue formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraIssueMarkdownFormatter()

    def test_format_issue_has_heading(self, formatter, sample_issue):
        """Should have markdown heading."""
        result = formatter.format(sample_issue)
        assert "##" in result or "**" in result

    def test_format_issue_has_table(self, formatter, sample_issue):
        """Should have markdown table."""
        result = formatter.format(sample_issue)
        assert "|" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Search Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraSearchAIFormatter:
    """Tests for AI-optimized search formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraSearchAIFormatter()

    def test_format_search_results(self, formatter, sample_search_results):
        """Should format search results concisely."""
        result = formatter.format(sample_search_results)

        assert "FOUND:" in result or "issues" in result.lower()
        assert "TEST-1" in result
        assert "TEST-2" in result

    def test_format_empty_results(self, formatter):
        """Should handle empty results."""
        result = formatter.format([])
        assert "0" in result or "no" in result.lower() or "empty" in result.lower()


class TestJiraSearchRichFormatter:
    """Tests for rich search formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraSearchRichFormatter()

    def test_format_search_results(self, formatter, sample_search_results):
        """Should format as table or list."""
        result = formatter.format(sample_search_results)
        assert "TEST-1" in result
        assert "TEST-2" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Transitions Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraTransitionsAIFormatter:
    """Tests for AI transitions formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraTransitionsAIFormatter()

    def test_format_transitions(self, formatter, sample_transitions):
        """Should list transitions concisely."""
        result = formatter.format(sample_transitions)

        assert "Start Progress" in result or "In Progress" in result
        assert "Resolve" in result or "Resolved" in result

    def test_format_empty_transitions(self, formatter):
        """Should handle no available transitions."""
        result = formatter.format([])
        assert "0" in result or "no" in result.lower()


class TestJiraTransitionsRichFormatter:
    """Tests for rich transitions formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraTransitionsRichFormatter()

    def test_format_transitions(self, formatter, sample_transitions):
        """Should format as table."""
        result = formatter.format(sample_transitions)
        assert "Start Progress" in result or "In Progress" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Comments Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraCommentsAIFormatter:
    """Tests for AI comments formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraCommentsAIFormatter()

    def test_format_comments(self, formatter, sample_comments):
        """Should format comments concisely."""
        result = formatter.format(sample_comments)

        assert "Alice" in result
        assert "Bob" in result

    def test_format_no_comments(self, formatter):
        """Should handle no comments."""
        result = formatter.format([])
        assert "no" in result.lower() or "0" in result


class TestJiraCommentsRichFormatter:
    """Tests for rich comments formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraCommentsRichFormatter()

    def test_format_comments(self, formatter, sample_comments):
        """Should format with author and date."""
        result = formatter.format(sample_comments)
        assert "Alice" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Registry Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFormatterRegistry:
    """Tests for formatter registration."""

    def test_register_jira_formatters(self):
        """Should register all jira formatters."""
        register_jira_formatters()

        # Check issue formatters
        assert formatter_registry.get("ai", plugin="jira", data_type="issue") is not None
        assert formatter_registry.get("rich", plugin="jira", data_type="issue") is not None

        # Check search formatters
        assert formatter_registry.get("ai", plugin="jira", data_type="search") is not None

        # Check transitions formatters
        assert formatter_registry.get("ai", plugin="jira", data_type="transitions") is not None

    def test_lookup_with_plugin_and_type(self):
        """Should find formatter by plugin and data type."""
        register_jira_formatters()
        formatter = formatter_registry.get("ai", plugin="jira", data_type="issue")
        assert formatter is not None
        assert isinstance(formatter, JiraIssueAIFormatter)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
