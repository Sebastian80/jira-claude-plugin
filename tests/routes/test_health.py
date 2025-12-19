"""
Tests for health and status endpoints.

Endpoints tested:
- jira health - Jira connection health
- jira status - Server status

Cross-cutting tests that verify the Jira server and connection are operational.
"""

import pytest

from helpers import run_cli, run_cli_raw, get_data


class TestJiraHealth:
    """Test Jira plugin /health endpoint."""

    def test_jira_health_basic(self):
        """Should return Jira connection health."""
        result = run_cli("jira", "health")
        data = get_data(result)
        assert data.get("status") == "healthy"
        assert data.get("connected") is True

    def test_jira_health_user_info(self):
        """Health should include user info."""
        result = run_cli("jira", "health")
        data = get_data(result)
        assert "user" in data
        assert data.get("user") is not None

    def test_jira_health_server_info(self):
        """Health should include server URL."""
        result = run_cli("jira", "health")
        data = get_data(result)
        assert "server" in data
        assert "jira" in data.get("server", "").lower()

    def test_jira_health_formats(self):
        """Should support multiple output formats."""
        for fmt in ["json", "rich", "ai", "markdown"]:
            stdout, stderr, code = run_cli_raw("jira", "health", "--format", fmt)
            assert code == 0


class TestServerStatus:
    """Test server status command."""

    def test_server_status(self):
        """Should report server as running."""
        stdout, stderr, code = run_cli_raw("jira", "status")
        assert code == 0
        # Server should be running since we're able to call it
        assert "running" in stdout.lower() or "pid" in stdout.lower()


class TestPluginHelp:
    """Test plugin-level help system."""

    def test_jira_help(self):
        """Should show jira help."""
        stdout, stderr, code = run_cli_raw("jira", "help")
        assert "issue" in stdout.lower() or "search" in stdout.lower()
        assert code == 0

    def test_jira_help_specific(self):
        """Should show help for specific command."""
        stdout, stderr, code = run_cli_raw("jira", "help", "issue")
        assert code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
