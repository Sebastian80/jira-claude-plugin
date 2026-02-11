"""
Tests for comment endpoints.

Endpoints tested:
- GET /comments/{key} - List comments on issue
- POST /comment/{key} - Add comment (write operation)
- DELETE /comment/{key}/{comment_id} - Delete comment (write operation)
"""

import json

import pytest

from helpers import TEST_ISSUE, run_cli, get_data, run_cli_raw


class TestListComments:
    """Test /comments/{key} endpoint."""

    def test_list_comments_basic(self):
        """Should list comments on an issue."""
        result = run_cli("jira", "comments", TEST_ISSUE)
        data = get_data(result)
        assert isinstance(data, list)

    def test_list_comments_with_limit(self):
        """Should respect limit parameter."""
        result = run_cli("jira", "comments", TEST_ISSUE, "--limit", "2")
        data = get_data(result)
        assert len(data) <= 2

    def test_list_comments_json_format(self):
        """Should return JSON format by default."""
        result = run_cli("jira", "comments", TEST_ISSUE, "--format", "json")
        data = get_data(result)
        assert isinstance(data, list)

    def test_list_comments_rich_format(self):
        """Should format comments for rich output."""
        stdout, stderr, code = run_cli_raw("jira", "comments", TEST_ISSUE, "--format", "rich")
        assert code == 0

    def test_list_comments_ai_format(self):
        """Should format comments for AI consumption."""
        stdout, stderr, code = run_cli_raw("jira", "comments", TEST_ISSUE, "--format", "ai")
        assert code == 0

    def test_list_comments_markdown_format(self):
        """Should format comments as markdown."""
        stdout, stderr, code = run_cli_raw("jira", "comments", TEST_ISSUE, "--format", "markdown")
        assert code == 0

    def test_list_comments_invalid_issue(self):
        """Should handle non-existent issue gracefully."""
        stdout, stderr, code = run_cli_raw("jira", "comments", "NONEXISTENT-99999")
        stdout_lower = stdout.lower()
        assert code != 0
        assert "not found" in stdout_lower or "error" in stdout_lower

    def test_list_comments_structure(self):
        """Comments should have expected structure if present."""
        result = run_cli("jira", "comments", TEST_ISSUE)
        data = get_data(result)
        if len(data) > 0:
            comment = data[0]
            assert "id" in comment or "body" in comment or "author" in comment


class TestCommentHelp:
    """Test comment help system."""

    def test_comments_help(self):
        """Should show help for comments command."""
        stdout, stderr, code = run_cli_raw("help", "comments")
        assert code == 0
        assert "comment" in stdout.lower()

    def test_comment_help(self):
        """Should show help for comment command."""
        stdout, stderr, code = run_cli_raw("help", "comment")
        assert code == 0
        assert "comment" in stdout.lower()


class TestAddComment:
    """Test /comment/{key} POST endpoint."""


    def test_add_comment(self):
        """Should add comment to issue."""
        result = run_cli("jira", "comment", TEST_ISSUE,
                        "--text", "[TEST] Auto-generated test comment")
        data = get_data(result)
        assert "id" in data or "self" in data


class TestDeleteComment:
    """Test /comment/{key}/{comment_id} DELETE endpoint."""


    def test_create_and_delete_comment(self):
        """Should create a comment, then delete it."""
        # Create a comment first
        result = run_cli("jira", "comment", TEST_ISSUE,
                        "--text", "[TEST] Comment to delete")
        data = get_data(result)
        comment_id = str(data["id"])

        # Delete the comment
        stdout, stderr, code = run_cli_raw(
            "jira", "comment", TEST_ISSUE, comment_id, "-X", "DELETE",
            "--format", "json")
        assert code == 0
        parsed = json.loads(stdout.strip())
        assert parsed.get("success") is True

        # Verify comment is gone
        result = run_cli("jira", "comments", TEST_ISSUE)
        comments = get_data(result)
        comment_ids = [str(c.get("id")) for c in comments]
        assert comment_id not in comment_ids


    def test_delete_nonexistent_comment(self):
        """Should return 404 for nonexistent comment ID."""
        stdout, stderr, code = run_cli_raw(
            "jira", "comment", TEST_ISSUE, "99999999", "-X", "DELETE",
            "--format", "json")
        output = stdout.strip() or stderr.strip()
        parsed = json.loads(output)
        assert parsed.get("success") is False or code != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
