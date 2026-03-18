"""
Tests for issue endpoints.

Endpoints tested:
- GET /issue/{key} - Get issue details
- POST /create - Create issue (skipped - write operation)
- PUT /issue/{key} - Update issue (skipped - write operation)
"""

import pytest

from helpers import TEST_PROJECT, TEST_ISSUE, run_cli, get_data, run_cli_raw, get_mock_client


class TestGetIssue:
    """Test /issue/{key} endpoint."""

    def test_get_issue_basic(self):
        """Should fetch issue details."""
        result = run_cli("jira", "issue", TEST_ISSUE)
        data = get_data(result)
        assert data.get("key") == TEST_ISSUE
        assert "fields" in data
        assert "summary" in data["fields"]

    def test_get_issue_with_fields(self):
        """Should fetch only specified fields."""
        result = run_cli("jira", "issue", TEST_ISSUE, "--fields", "summary,status")
        data = get_data(result)
        assert data.get("key") == TEST_ISSUE
        assert "summary" in data.get("fields", {})

    def test_get_issue_json_format(self):
        """Should return JSON format by default."""
        result = run_cli("jira", "issue", TEST_ISSUE, "--format", "json")
        data = get_data(result)
        assert data.get("key") == TEST_ISSUE

    def test_get_issue_rich_format(self):
        """Should format issue for rich output."""
        stdout, stderr, code = run_cli_raw("jira", "issue", TEST_ISSUE, "--format", "rich")
        assert TEST_ISSUE in stdout
        assert code == 0

    def test_get_issue_ai_format(self):
        """Should format issue for AI consumption."""
        stdout, stderr, code = run_cli_raw("jira", "issue", TEST_ISSUE, "--format", "ai")
        assert code == 0

    def test_get_issue_markdown_format(self):
        """Should format issue as markdown."""
        stdout, stderr, code = run_cli_raw("jira", "issue", TEST_ISSUE, "--format", "markdown")
        assert code == 0

    def test_get_issue_not_found(self):
        """Should handle non-existent issue gracefully."""
        stdout, stderr, code = run_cli_raw("jira", "issue", "NONEXISTENT-99999")
        stdout_lower = stdout.lower()
        assert code != 0
        assert "not found" in stdout_lower or "error" in stdout_lower

    def test_get_issue_invalid_key_format(self):
        """Should handle invalid issue key format."""
        stdout, stderr, code = run_cli_raw("jira", "issue", "not-a-valid-key")
        stdout_lower = stdout.lower()
        assert code != 0
        assert "not found" in stdout_lower or "error" in stdout_lower


class TestIssueHelp:
    """Test issue help system."""

    def test_issue_help(self):
        """Should show help for issue command."""
        stdout, stderr, code = run_cli_raw("help", "issue")
        assert code == 0
        assert "issue" in stdout.lower()


class TestCreateIssue:
    """Test /create endpoint."""

    def test_create_issue(self):
        """Should create a new issue."""
        result = run_cli("jira", "create",
                        "--project", TEST_PROJECT,
                        "--type", "Task",
                        "--summary", "[TEST] Auto-generated test issue - please delete")
        data = get_data(result)
        assert "key" in data
        print(f"Created issue: {data['key']}")

    def test_create_help(self):
        """Should show create command help."""
        stdout, stderr, code = run_cli_raw("help", "create")
        assert code == 0
        assert "create" in stdout.lower()
        # Verify key parameters are documented
        assert "project" in stdout.lower() or "summary" in stdout.lower()


class TestUpdateIssue:
    """Test /issue/{key} PATCH endpoint."""

    def test_update_issue_summary(self):
        """Should update issue summary."""
        result = run_cli("jira", "update", TEST_ISSUE, "--summary", "Updated summary")
        data = get_data(result)
        assert data["key"] == TEST_ISSUE
        assert "summary" in data["updated"]

    def test_update_issue_clear_description(self):
        """Should be able to clear description with empty string."""
        mock = get_mock_client()
        mock._call_log.clear()

        result = run_cli("jira", "update", TEST_ISSUE, "--description", "")
        data = get_data(result)
        assert data["key"] == TEST_ISSUE
        assert "description" in data["updated"]

        # Verify the empty string was sent to the client
        update_calls = [c for c in mock._call_log if c[0] == "update_issue_field"]
        assert update_calls, "Expected update_issue_field call"
        fields = update_calls[0][2]
        assert "description" in fields
        assert fields["description"] == ""


class TestUpdateIssueValidation:
    """Test update validation edge cases."""

    def test_update_accepts_empty_string_fields(self):
        """Validator should accept empty strings as valid field values."""
        from jira.routes.issues import UpdateIssueBody
        # Empty string should NOT be rejected by the validator
        body = UpdateIssueBody(description="")
        assert body.description == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
