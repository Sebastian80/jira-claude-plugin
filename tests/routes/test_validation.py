"""
Tests for CLI parameter validation.

Tests verify that the CLI and API handle invalid inputs gracefully.
"""

import pytest

from helpers import TEST_PROJECT, run_cli_raw


class TestParameterValidation:
    """Test CLI parameter validation."""

    def test_missing_required_param(self):
        """Should return error for missing required params."""
        stdout, stderr, code = run_cli_raw("search")
        combined_lower = (stdout + stderr).lower()
        # API returns field validation error for missing JQL
        assert "required" in combined_lower or "jql" in combined_lower or code != 0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_command(self):
        """Should handle invalid command gracefully."""
        stdout, stderr, code = run_cli_raw("nonexistent_command_12345")
        stdout_lower = stdout.lower()
        # Should return error or "not found"
        assert code != 0 or "not found" in stdout_lower or "endpoint" in stdout_lower

    def test_invalid_issue_key(self):
        """Should handle invalid issue key format."""
        stdout, stderr, code = run_cli_raw("issue", "invalid-key-format")
        stdout_lower = stdout.lower()
        assert code != 0 or "not found" in stdout_lower or "error" in stdout_lower or "detail" in stdout_lower


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
