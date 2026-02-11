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
    JiraCommentsMarkdownFormatter,
    JiraAttachmentsRichFormatter,
    JiraAttachmentsAIFormatter,
    JiraHealthRichFormatter,
    JiraHealthAIFormatter,
    JiraHealthMarkdownFormatter,
    JiraLinksRichFormatter,
    JiraLinksAIFormatter,
    JiraLinkTypesRichFormatter,
    JiraLinkTypesAIFormatter,
    JiraPrioritiesRichFormatter,
    JiraPrioritiesAIFormatter,
    JiraPrioritiesMarkdownFormatter,
    JiraStatusesRichFormatter,
    JiraStatusesAIFormatter,
    JiraStatusesMarkdownFormatter,
    JiraUserRichFormatter,
    JiraUserAIFormatter,
    JiraUserMarkdownFormatter,
    JiraWatchersRichFormatter,
    JiraWatchersAIFormatter,
    JiraWebLinksRichFormatter,
    JiraWebLinksAIFormatter,
    JiraWorklogsRichFormatter,
    JiraWorklogsAIFormatter,
    JiraShowRichFormatter,
    JiraShowAIFormatter,
    JiraShowMarkdownFormatter,
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

    def test_formatters_auto_registered(self):
        """Formatters are auto-registered via decorators on import."""
        # Check issue formatters
        assert formatter_registry.get("ai", plugin="jira", data_type="issue") is not None
        assert formatter_registry.get("rich", plugin="jira", data_type="issue") is not None

        # Check search formatters
        assert formatter_registry.get("ai", plugin="jira", data_type="search") is not None

        # Check transitions formatters
        assert formatter_registry.get("ai", plugin="jira", data_type="transitions") is not None

    def test_lookup_with_plugin_and_type(self):
        """Should find formatter by plugin and data type."""
        formatter = formatter_registry.get("ai", plugin="jira", data_type="issue")
        assert formatter is not None
        assert isinstance(formatter, JiraIssueAIFormatter)


# ═══════════════════════════════════════════════════════════════════════════════
# Comments Markdown Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraCommentsMarkdownFormatter:
    """Tests for markdown comments formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraCommentsMarkdownFormatter()

    def test_format_comments(self, formatter, sample_comments):
        """Should format comments with markdown headings and separators."""
        result = formatter.format(sample_comments)

        assert "## Comments (2)" in result
        assert "### Alice" in result
        assert "### Bob" in result
        assert "2024-01-15" in result
        assert "test comment from Alice" in result
        assert "---" in result

    def test_format_no_comments(self, formatter):
        """Should show no-comments message."""
        result = formatter.format([])
        assert "No comments" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Search Markdown Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraSearchMarkdownFormatter:
    """Tests for markdown search formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraSearchMarkdownFormatter()

    def test_format_search_results(self, formatter, sample_search_results):
        """Should format as markdown table with key, status, and summary."""
        result = formatter.format(sample_search_results)

        assert "| Key |" in result
        assert "TEST-1" in result
        assert "TEST-2" in result
        assert "Open" in result
        assert "Closed" in result

    def test_format_empty_results(self, formatter):
        """Should show no-issues message."""
        result = formatter.format([])
        assert "No issues found" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Attachments Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraAttachmentsRichFormatter:
    """Tests for rich attachments formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraAttachmentsRichFormatter()

    @pytest.fixture
    def sample_attachments(self):
        return [
            {
                "id": "10200",
                "filename": "test-file.txt",
                "size": 1024,
                "mimeType": "text/plain",
                "author": {"displayName": "Test User"},
            },
        ]

    def test_format_attachments(self, formatter, sample_attachments):
        """Should format attachments as table with filename, size, author."""
        result = formatter.format(sample_attachments)

        assert "test-file.txt" in result
        assert "Test User" in result
        assert "Attachments" in result

    def test_format_no_attachments(self, formatter):
        """Should show no-attachments message."""
        result = formatter.format([])
        assert "No attachments" in result


class TestJiraAttachmentsAIFormatter:
    """Tests for AI attachments formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraAttachmentsAIFormatter()

    @pytest.fixture
    def sample_attachments(self):
        return [
            {
                "id": "10200",
                "filename": "test-file.txt",
                "size": 1024,
                "mimeType": "text/plain",
                "author": {"displayName": "Test User"},
            },
        ]

    def test_format_attachments(self, formatter, sample_attachments):
        """Should format attachments concisely."""
        result = formatter.format(sample_attachments)

        assert "ATTACHMENTS: 1" in result
        assert "test-file.txt" in result
        assert "1024" in result

    def test_format_no_attachments(self, formatter):
        """Should return NO_ATTACHMENTS."""
        result = formatter.format([])
        assert "NO_ATTACHMENTS" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Health Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraHealthRichFormatter:
    """Tests for rich health formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraHealthRichFormatter()

    @pytest.fixture
    def sample_health(self):
        return {
            "status": "ok",
            "connected": True,
            "user": "test.user",
            "server": "https://jira.example.com",
        }

    def test_format_healthy(self, formatter, sample_health):
        """Should show healthy status with user and server."""
        result = formatter.format(sample_health)

        assert "Healthy" in result
        assert "test.user" in result
        assert "jira.example.com" in result

    def test_format_unhealthy(self, formatter):
        """Should show unhealthy status with error."""
        data = {
            "status": "error",
            "connected": False,
            "error": "Connection refused",
            "server": "https://jira.example.com",
        }
        result = formatter.format(data)
        assert "Unhealthy" in result
        assert "Connection refused" in result


class TestJiraHealthAIFormatter:
    """Tests for AI health formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraHealthAIFormatter()

    @pytest.fixture
    def sample_health(self):
        return {
            "status": "ok",
            "connected": True,
            "user": "test.user",
            "server": "https://jira.example.com",
        }

    def test_format_healthy(self, formatter, sample_health):
        """Should format health status concisely."""
        result = formatter.format(sample_health)

        assert "HEALTH: ok" in result
        assert "connected: true" in result
        assert "user: test.user" in result
        assert "server:" in result

    def test_format_unhealthy_with_error(self, formatter):
        """Should include error in output."""
        data = {
            "status": "error",
            "connected": False,
            "error": "Auth failed",
        }
        result = formatter.format(data)
        assert "HEALTH: error" in result
        assert "connected: false" in result
        assert "error: Auth failed" in result


class TestJiraHealthMarkdownFormatter:
    """Tests for markdown health formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraHealthMarkdownFormatter()

    @pytest.fixture
    def sample_health(self):
        return {
            "status": "ok",
            "connected": True,
            "user": "test.user",
            "server": "https://jira.example.com",
        }

    def test_format_healthy(self, formatter, sample_health):
        """Should format as markdown table with heading."""
        result = formatter.format(sample_health)

        assert "## Jira Health:" in result
        assert "| Connected | Yes |" in result
        assert "| User | test.user |" in result
        assert "| Server |" in result

    def test_format_unhealthy(self, formatter):
        """Should show unhealthy status in markdown."""
        data = {
            "status": "error",
            "connected": False,
            "error": "Timeout",
        }
        result = formatter.format(data)
        assert "| Connected | No |" in result
        assert "| Error | Timeout |" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Links Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraLinksRichFormatter:
    """Tests for rich issue links formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraLinksRichFormatter()

    @pytest.fixture
    def sample_links(self):
        return [
            {
                "id": "10300",
                "type": {"name": "Blocks", "inward": "is blocked by", "outward": "blocks"},
                "outwardIssue": {
                    "key": "HMKG-2063",
                    "fields": {"summary": "Linked issue", "status": {"name": "Open"}},
                },
            },
        ]

    def test_format_links(self, formatter, sample_links):
        """Should format links as table with relationship and linked issue."""
        result = formatter.format(sample_links)

        assert "blocks" in result
        assert "HMKG-2063" in result
        assert "Linked issue" in result

    def test_format_no_links(self, formatter):
        """Should show no-links message."""
        result = formatter.format([])
        assert "No links" in result


class TestJiraLinksAIFormatter:
    """Tests for AI issue links formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraLinksAIFormatter()

    @pytest.fixture
    def sample_links(self):
        return [
            {
                "id": "10300",
                "type": {"name": "Blocks", "inward": "is blocked by", "outward": "blocks"},
                "outwardIssue": {
                    "key": "HMKG-2063",
                    "fields": {"summary": "Linked issue", "status": {"name": "Open"}},
                },
            },
        ]

    def test_format_links(self, formatter, sample_links):
        """Should format links concisely with direction."""
        result = formatter.format(sample_links)

        assert "LINKS: 1" in result
        assert "blocks" in result
        assert "HMKG-2063" in result

    def test_format_no_links(self, formatter):
        """Should return NO_LINKS."""
        result = formatter.format([])
        assert "NO_LINKS" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Link Types Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraLinkTypesRichFormatter:
    """Tests for rich link types formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraLinkTypesRichFormatter()

    @pytest.fixture
    def sample_linktypes(self):
        return [
            {"id": "10000", "name": "Blocks", "inward": "is blocked by", "outward": "blocks"},
            {"id": "10001", "name": "Cloners", "inward": "is cloned by", "outward": "clones"},
        ]

    def test_format_linktypes(self, formatter, sample_linktypes):
        """Should format link types as table."""
        result = formatter.format(sample_linktypes)

        assert "Blocks" in result
        assert "Cloners" in result
        assert "blocks" in result
        assert "clones" in result

    def test_format_empty_data_falls_back(self, formatter):
        """Should fall back for data without 'inward' key."""
        result = formatter.format([{"something": "else"}])
        # Falls through to super().format() -- returns str representation
        assert result is not None


class TestJiraLinkTypesAIFormatter:
    """Tests for AI link types formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraLinkTypesAIFormatter()

    @pytest.fixture
    def sample_linktypes(self):
        return [
            {"id": "10000", "name": "Blocks", "inward": "is blocked by", "outward": "blocks"},
            {"id": "10001", "name": "Cloners", "inward": "is cloned by", "outward": "clones"},
        ]

    def test_format_linktypes(self, formatter, sample_linktypes):
        """Should format link types concisely."""
        result = formatter.format(sample_linktypes)

        assert "LINK_TYPES: 2" in result
        assert "Blocks" in result
        assert "blocks / is blocked by" in result

    def test_format_empty_data_falls_back(self, formatter):
        """Should fall back for data without 'inward' key."""
        result = formatter.format([{"something": "else"}])
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Priorities Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraPrioritiesRichFormatter:
    """Tests for rich priorities formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraPrioritiesRichFormatter()

    @pytest.fixture
    def sample_priorities(self):
        return [
            {"id": "1", "name": "Highest", "iconUrl": "https://jira.example.com/icon1.png"},
            {"id": "2", "name": "High", "iconUrl": "https://jira.example.com/icon2.png"},
            {"id": "3", "name": "Medium", "iconUrl": "https://jira.example.com/icon3.png"},
        ]

    def test_format_priorities(self, formatter, sample_priorities):
        """Should format priorities as table."""
        result = formatter.format(sample_priorities)

        assert "Highest" in result
        assert "High" in result
        assert "Medium" in result

    def test_format_non_priority_data_falls_back(self, formatter):
        """Should fall back for data without 'iconUrl' key."""
        result = formatter.format([{"name": "something"}])
        assert result is not None


class TestJiraPrioritiesAIFormatter:
    """Tests for AI priorities formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraPrioritiesAIFormatter()

    @pytest.fixture
    def sample_priorities(self):
        return [
            {"id": "1", "name": "Highest", "iconUrl": "https://jira.example.com/icon1.png"},
            {"id": "2", "name": "High", "iconUrl": "https://jira.example.com/icon2.png"},
        ]

    def test_format_priorities(self, formatter, sample_priorities):
        """Should format priorities concisely."""
        result = formatter.format(sample_priorities)

        assert "PRIORITIES: 2" in result
        assert "Highest" in result
        assert "id:1" in result

    def test_format_non_priority_data_falls_back(self, formatter):
        """Should fall back for data without 'iconUrl' key."""
        result = formatter.format([{"name": "something"}])
        assert result is not None


class TestJiraPrioritiesMarkdownFormatter:
    """Tests for markdown priorities formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraPrioritiesMarkdownFormatter()

    @pytest.fixture
    def sample_priorities(self):
        return [
            {"id": "1", "name": "Highest", "iconUrl": "https://jira.example.com/icon1.png"},
            {"id": "2", "name": "High", "iconUrl": "https://jira.example.com/icon2.png"},
        ]

    def test_format_priorities(self, formatter, sample_priorities):
        """Should format as markdown table."""
        result = formatter.format(sample_priorities)

        assert "## Jira Priorities" in result
        assert "| Name | ID |" in result
        assert "| Highest | 1 |" in result
        assert "| High | 2 |" in result

    def test_format_non_priority_data_falls_back(self, formatter):
        """Should fall back for data without 'iconUrl' key."""
        result = formatter.format([{"name": "something"}])
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Statuses Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraStatusesRichFormatter:
    """Tests for rich statuses formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraStatusesRichFormatter()

    @pytest.fixture
    def sample_statuses(self):
        return [
            {"id": "1", "name": "Open", "statusCategory": {"name": "To Do"}},
            {"id": "3", "name": "In Progress", "statusCategory": {"name": "In Progress"}},
            {"id": "5", "name": "Done", "statusCategory": {"name": "Done"}},
        ]

    def test_format_statuses(self, formatter, sample_statuses):
        """Should format statuses as table with category."""
        result = formatter.format(sample_statuses)

        assert "Open" in result
        assert "In Progress" in result
        assert "Done" in result

    def test_format_non_status_data_falls_back(self, formatter):
        """Should fall back for data without 'statusCategory' key."""
        result = formatter.format([{"name": "something"}])
        assert result is not None


class TestJiraStatusesAIFormatter:
    """Tests for AI statuses formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraStatusesAIFormatter()

    @pytest.fixture
    def sample_statuses(self):
        return [
            {"id": "1", "name": "Open", "statusCategory": {"name": "To Do"}},
            {"id": "3", "name": "In Progress", "statusCategory": {"name": "In Progress"}},
            {"id": "5", "name": "Done", "statusCategory": {"name": "Done"}},
        ]

    def test_format_statuses(self, formatter, sample_statuses):
        """Should format statuses grouped by category."""
        result = formatter.format(sample_statuses)

        assert "STATUSES: 3" in result
        assert "To Do" in result
        assert "In Progress" in result
        assert "Done" in result

    def test_format_non_status_data_falls_back(self, formatter):
        """Should fall back for data without 'statusCategory' key."""
        result = formatter.format([{"name": "something"}])
        assert result is not None


class TestJiraStatusesMarkdownFormatter:
    """Tests for markdown statuses formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraStatusesMarkdownFormatter()

    @pytest.fixture
    def sample_statuses(self):
        return [
            {"id": "1", "name": "Open", "statusCategory": {"name": "To Do"}},
            {"id": "5", "name": "Done", "statusCategory": {"name": "Done"}},
        ]

    def test_format_statuses(self, formatter, sample_statuses):
        """Should format as markdown table."""
        result = formatter.format(sample_statuses)

        assert "## Jira Statuses" in result
        assert "| Name | Category | ID |" in result
        assert "| Open | To Do | 1 |" in result
        assert "| Done | Done | 5 |" in result

    def test_format_non_status_data_falls_back(self, formatter):
        """Should fall back for data without 'statusCategory' key."""
        result = formatter.format([{"name": "something"}])
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════════
# User Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraUserRichFormatter:
    """Tests for rich user formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraUserRichFormatter()

    @pytest.fixture
    def sample_user(self):
        return {
            "name": "test.user",
            "displayName": "Test User",
            "emailAddress": "test.user@example.com",
            "active": True,
        }

    def test_format_user(self, formatter, sample_user):
        """Should format user with name, email, and status."""
        result = formatter.format(sample_user)

        assert "Test User" in result
        assert "test.user" in result
        assert "test.user@example.com" in result
        assert "Active" in result

    def test_format_inactive_user(self, formatter):
        """Should show inactive status."""
        data = {
            "displayName": "Gone User",
            "emailAddress": "gone@example.com",
            "active": False,
        }
        result = formatter.format(data)
        assert "Inactive" in result


class TestJiraUserAIFormatter:
    """Tests for AI user formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraUserAIFormatter()

    @pytest.fixture
    def sample_user(self):
        return {
            "name": "test.user",
            "displayName": "Test User",
            "emailAddress": "test.user@example.com",
            "active": True,
        }

    def test_format_user(self, formatter, sample_user):
        """Should format user concisely."""
        result = formatter.format(sample_user)

        assert "USER: test.user" in result
        assert "name: Test User" in result
        assert "email: test.user@example.com" in result
        assert "active: true" in result

    def test_format_user_minimal(self, formatter):
        """Should handle user with minimal fields."""
        data = {"displayName": "Minimal User"}
        result = formatter.format(data)
        assert "name: Minimal User" in result


class TestJiraUserMarkdownFormatter:
    """Tests for markdown user formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraUserMarkdownFormatter()

    @pytest.fixture
    def sample_user(self):
        return {
            "name": "test.user",
            "displayName": "Test User",
            "emailAddress": "test.user@example.com",
            "active": True,
        }

    def test_format_user(self, formatter, sample_user):
        """Should format as markdown table."""
        result = formatter.format(sample_user)

        assert "## User: Test User" in result
        assert "| Username | test.user |" in result
        assert "| Email | test.user@example.com |" in result
        assert "| Active | Yes |" in result

    def test_format_inactive_user(self, formatter):
        """Should show 'No' for inactive user."""
        data = {
            "displayName": "Gone User",
            "emailAddress": "gone@example.com",
            "active": False,
        }
        result = formatter.format(data)
        assert "| Active | No |" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Watchers Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraWatchersRichFormatter:
    """Tests for rich watchers formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraWatchersRichFormatter()

    @pytest.fixture
    def sample_watchers(self):
        return {
            "watchCount": 2,
            "isWatching": True,
            "watchers": [
                {"name": "test.user", "displayName": "Test User"},
                {"name": "alice", "displayName": "Alice"},
            ],
        }

    def test_format_watchers(self, formatter, sample_watchers):
        """Should format watchers as table."""
        result = formatter.format(sample_watchers)

        assert "Test User" in result
        assert "Alice" in result
        assert "Watchers" in result

    def test_format_no_watchers(self, formatter):
        """Should show no-watchers message."""
        data = {"watchCount": 0, "watchers": []}
        result = formatter.format(data)
        assert "No watchers" in result or "0" in result


class TestJiraWatchersAIFormatter:
    """Tests for AI watchers formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraWatchersAIFormatter()

    @pytest.fixture
    def sample_watchers(self):
        return {
            "watchCount": 2,
            "isWatching": True,
            "watchers": [
                {"name": "test.user", "displayName": "Test User"},
                {"name": "alice", "displayName": "Alice"},
            ],
        }

    def test_format_watchers(self, formatter, sample_watchers):
        """Should format watchers concisely."""
        result = formatter.format(sample_watchers)

        assert "WATCHERS: 2" in result
        assert "Test User" in result
        assert "Alice" in result

    def test_format_no_watchers(self, formatter):
        """Should indicate zero watchers."""
        data = {"watchCount": 0, "watchers": []}
        result = formatter.format(data)
        assert "WATCHERS: 0" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Web Links Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraWebLinksRichFormatter:
    """Tests for rich web links formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraWebLinksRichFormatter()

    @pytest.fixture
    def sample_weblinks(self):
        return [
            {
                "id": 10900,
                "object": {"url": "https://example.com", "title": "Example Website"},
            },
        ]

    def test_format_weblinks(self, formatter, sample_weblinks):
        """Should format web links as table with title and URL."""
        result = formatter.format(sample_weblinks)

        assert "Example Website" in result
        assert "example.com" in result
        assert "Web Links" in result

    def test_format_no_weblinks(self, formatter):
        """Should show no-weblinks message."""
        result = formatter.format([])
        assert "No web links" in result


class TestJiraWebLinksAIFormatter:
    """Tests for AI web links formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraWebLinksAIFormatter()

    @pytest.fixture
    def sample_weblinks(self):
        return [
            {
                "id": 10900,
                "object": {"url": "https://example.com", "title": "Example Website"},
            },
        ]

    def test_format_weblinks(self, formatter, sample_weblinks):
        """Should format web links concisely."""
        result = formatter.format(sample_weblinks)

        assert "WEBLINKS: 1" in result
        assert "Example Website" in result
        assert "https://example.com" in result

    def test_format_no_weblinks(self, formatter):
        """Should return NO_WEBLINKS."""
        result = formatter.format([])
        assert "NO_WEBLINKS" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Worklogs Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraWorklogsRichFormatter:
    """Tests for rich worklogs formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraWorklogsRichFormatter()

    @pytest.fixture
    def sample_worklogs(self):
        return [
            {
                "id": "10400",
                "author": {"displayName": "Test User"},
                "timeSpent": "2h",
                "timeSpentSeconds": 7200,
                "comment": "Worked on implementation",
                "started": "2024-01-15T09:00:00.000+0000",
            },
        ]

    def test_format_worklogs(self, formatter, sample_worklogs):
        """Should format worklogs as table with author, time, date."""
        result = formatter.format(sample_worklogs)

        assert "Test User" in result
        assert "2h" in result
        assert "2024-01-15" in result
        assert "Worklogs" in result

    def test_format_no_worklogs(self, formatter):
        """Should show no-worklogs message."""
        result = formatter.format([])
        assert "No worklogs" in result


class TestJiraWorklogsAIFormatter:
    """Tests for AI worklogs formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraWorklogsAIFormatter()

    @pytest.fixture
    def sample_worklogs(self):
        return [
            {
                "id": "10400",
                "author": {"displayName": "Test User"},
                "timeSpent": "2h",
                "timeSpentSeconds": 7200,
                "comment": "Worked on implementation",
                "started": "2024-01-15T09:00:00.000+0000",
            },
        ]

    def test_format_worklogs(self, formatter, sample_worklogs):
        """Should format worklogs concisely."""
        result = formatter.format(sample_worklogs)

        assert "WORKLOGS: 1" in result
        assert "Test User" in result
        assert "2h" in result
        assert "2024-01-15" in result

    def test_format_no_worklogs(self, formatter):
        """Should return NO_WORKLOGS."""
        result = formatter.format([])
        assert "NO_WORKLOGS" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Show (Combined Issue + Comments) Formatter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraShowRichFormatter:
    """Tests for rich combined issue+comments formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraShowRichFormatter()

    @pytest.fixture
    def sample_show_data(self, sample_issue, sample_comments):
        return {"issue": sample_issue, "comments": sample_comments}

    def test_format_show(self, formatter, sample_show_data):
        """Should show issue details and comments together."""
        result = formatter.format(sample_show_data)

        # Issue parts
        assert "TEST-123" in result
        assert "Sample test issue summary" in result
        # Comments parts
        assert "Comments (2)" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_format_show_no_comments(self, formatter, sample_issue):
        """Should handle issue with no comments."""
        data = {"issue": sample_issue, "comments": []}
        result = formatter.format(data)

        assert "TEST-123" in result
        assert "No comments" in result


class TestJiraShowAIFormatter:
    """Tests for AI combined issue+comments formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraShowAIFormatter()

    @pytest.fixture
    def sample_show_data(self, sample_issue, sample_comments):
        return {"issue": sample_issue, "comments": sample_comments}

    def test_format_show(self, formatter, sample_show_data):
        """Should show issue and comments concisely."""
        result = formatter.format(sample_show_data)

        assert "ISSUE: TEST-123" in result
        assert "comments: 2" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_format_show_no_comments(self, formatter, sample_issue):
        """Should handle issue with no comments."""
        data = {"issue": sample_issue, "comments": []}
        result = formatter.format(data)

        assert "ISSUE: TEST-123" in result
        assert "comments: 0" in result


class TestJiraShowMarkdownFormatter:
    """Tests for markdown combined issue+comments formatting."""

    @pytest.fixture
    def formatter(self):
        return JiraShowMarkdownFormatter()

    @pytest.fixture
    def sample_show_data(self, sample_issue, sample_comments):
        return {"issue": sample_issue, "comments": sample_comments}

    def test_format_show(self, formatter, sample_show_data):
        """Should show issue and comments in markdown."""
        result = formatter.format(sample_show_data)

        assert "TEST-123" in result
        assert "### Comments (2)" in result
        assert "**Alice**" in result
        assert "**Bob**" in result

    def test_format_show_no_comments(self, formatter, sample_issue):
        """Should handle issue with no comments."""
        data = {"issue": sample_issue, "comments": []}
        result = formatter.format(data)

        assert "TEST-123" in result
        assert "### Comments (0)" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
