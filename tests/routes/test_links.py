"""
Tests for link endpoints.

Endpoints tested:
- GET /links/{key} - List issue links on an issue
- GET /linktypes - List available link types (convenient alias)
- GET /link/types - List available link types
- POST /link - Create issue link (skipped - write operation)
- GET /weblinks/{key} - List web links on issue
- POST /weblink/{key} - Add web link (skipped - write operation)
"""

import pytest

from helpers import TEST_ISSUE, run_cli, get_data, run_cli_raw


class TestIssueLinks:
    """Test /links/{key} endpoint."""

    def test_list_issue_links_basic(self):
        """Should list issue links on an issue."""
        result = run_cli("jira", "links", TEST_ISSUE)
        data = get_data(result)
        assert isinstance(data, list)

    def test_list_issue_links_json_format(self):
        """Should return JSON format by default."""
        result = run_cli("jira", "links", TEST_ISSUE, "--format", "json")
        data = get_data(result)
        assert isinstance(data, list)

    def test_list_issue_links_rich_format(self):
        """Should format links for rich output."""
        stdout, stderr, code = run_cli_raw("jira", "links", TEST_ISSUE, "--format", "rich")
        assert code == 0

    def test_list_issue_links_ai_format(self):
        """Should format links for AI consumption."""
        stdout, stderr, code = run_cli_raw("jira", "links", TEST_ISSUE, "--format", "ai")
        assert code == 0

    def test_list_issue_links_markdown_format(self):
        """Should format links as markdown."""
        stdout, stderr, code = run_cli_raw("jira", "links", TEST_ISSUE, "--format", "markdown")
        assert code == 0

    def test_list_issue_links_structure(self):
        """Links should have expected structure if present."""
        result = run_cli("jira", "links", TEST_ISSUE)
        data = get_data(result)
        if len(data) > 0:
            link = data[0]
            # Links have: type, inwardIssue or outwardIssue
            assert "type" in link or "id" in link

    def test_list_issue_links_invalid_issue(self):
        """Should handle non-existent issue gracefully."""
        stdout, stderr, code = run_cli_raw("jira", "links", "NONEXISTENT-99999")
        stdout_lower = stdout.lower()
        assert code != 0
        assert "not found" in stdout_lower or "error" in stdout_lower


class TestLinkTypes:
    """Test /linktypes and /link/types endpoints."""

    def test_linktypes_basic(self):
        """Should list available link types via /linktypes."""
        result = run_cli("jira", "linktypes")
        data = get_data(result)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_linktypes_json_format(self):
        """Should return JSON format by default."""
        result = run_cli("jira", "linktypes", "--format", "json")
        data = get_data(result)
        assert isinstance(data, list)

    def test_linktypes_rich_format(self):
        """Should format link types for rich output."""
        stdout, stderr, code = run_cli_raw("jira", "linktypes", "--format", "rich")
        assert code == 0

    def test_linktypes_structure(self):
        """Link types should have expected structure."""
        result = run_cli("jira", "linktypes")
        data = get_data(result)
        assert len(data) > 0
        link_type = data[0]
        assert "name" in link_type
        assert "inward" in link_type or "outward" in link_type

    def test_link_types_alias(self):
        """Should also work via /link/types alias."""
        result = run_cli("jira", "link/types")
        data = get_data(result)
        assert isinstance(data, list)
        assert len(data) > 0


class TestWebLinks:
    """Test /weblinks/{key} endpoint."""

    def test_list_weblinks_basic(self):
        """Should list web links on an issue."""
        result = run_cli("jira", "weblinks", TEST_ISSUE)
        data = get_data(result)
        assert isinstance(data, list)

    def test_list_weblinks_json_format(self):
        """Should return JSON format by default."""
        result = run_cli("jira", "weblinks", TEST_ISSUE, "--format", "json")
        data = get_data(result)
        assert isinstance(data, list)

    def test_list_weblinks_rich_format(self):
        """Should format web links for rich output."""
        stdout, stderr, code = run_cli_raw("jira", "weblinks", TEST_ISSUE, "--format", "rich")
        assert code == 0

    def test_list_weblinks_invalid_issue(self):
        """Should handle non-existent issue gracefully."""
        stdout, stderr, code = run_cli_raw("jira", "weblinks", "NONEXISTENT-99999")
        stdout_lower = stdout.lower()
        assert code != 0
        assert "not found" in stdout_lower or "error" in stdout_lower


class TestLinkHelp:
    """Test link help system."""

    def test_links_help(self):
        """Should show help for links command."""
        stdout, stderr, code = run_cli_raw("help", "links")
        assert code == 0
        assert "link" in stdout.lower()

    def test_linktypes_help(self):
        """Should show help for linktypes command."""
        stdout, stderr, code = run_cli_raw("help", "linktypes")
        assert code == 0
        assert "link" in stdout.lower()

    def test_link_help(self):
        """Should show help for link command."""
        stdout, stderr, code = run_cli_raw("help", "link")
        assert code == 0
        assert "link" in stdout.lower()

    def test_weblinks_help(self):
        """Should show help for weblinks command."""
        stdout, stderr, code = run_cli_raw("help", "weblinks")
        assert code == 0
        assert "weblink" in stdout.lower()


class TestCreateLink:
    """Test /link POST endpoint."""


    def test_create_link(self):
        """Should create issue link."""
        result = run_cli("jira", "link",
                        "--from", TEST_ISSUE, "--to", "HMKG-2063", "--type", "Blocks")
        data = get_data(result)
        assert data.get("from") == TEST_ISSUE
        assert data.get("type") == "Blocks"


class TestCreateWebLink:
    """Test /weblink/{key} POST endpoint."""


    def test_create_weblink(self):
        """Should create web link on issue."""
        result = run_cli("jira", "weblink", TEST_ISSUE,
                        "--url", "https://example.com", "--title", "Example")
        data = get_data(result)
        assert data.get("key") == TEST_ISSUE
        assert data.get("url") == "https://example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
