"""Tests for environment configuration handling."""

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from jira.lib.config import load_env, validate_config, get_auth_mode


class TestLoadEnv:
    """Tests for load_env()."""

    def test_reads_key_value_pairs(self, tmp_path):
        """Should parse key=value lines from env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("JIRA_URL=https://test.atlassian.net\nJIRA_USERNAME=user\n")

        config = load_env(str(env_file))

        assert config["JIRA_URL"] == "https://test.atlassian.net"
        assert config["JIRA_USERNAME"] == "user"

    def test_strips_double_quotes(self, tmp_path):
        """Should strip surrounding double quotes from values."""
        env_file = tmp_path / ".env"
        env_file.write_text('JIRA_URL="https://test.atlassian.net"\n')

        config = load_env(str(env_file))

        assert config["JIRA_URL"] == "https://test.atlassian.net"

    def test_strips_single_quotes(self, tmp_path):
        """Should strip surrounding single quotes from values."""
        env_file = tmp_path / ".env"
        env_file.write_text("JIRA_URL='https://test.atlassian.net'\n")

        config = load_env(str(env_file))

        assert config["JIRA_URL"] == "https://test.atlassian.net"

    def test_ignores_comments(self, tmp_path):
        """Should skip lines starting with #."""
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nJIRA_URL=https://test.atlassian.net\n")

        config = load_env(str(env_file))

        assert "# This is a comment" not in config
        assert config["JIRA_URL"] == "https://test.atlassian.net"

    def test_ignores_empty_lines(self, tmp_path):
        """Should skip blank lines without error."""
        env_file = tmp_path / ".env"
        env_file.write_text("\nJIRA_URL=https://test.atlassian.net\n\n")

        config = load_env(str(env_file))

        assert config["JIRA_URL"] == "https://test.atlassian.net"
        assert len(config) == 1

    def test_explicit_missing_file_raises(self):
        """Should raise FileNotFoundError when explicit file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Environment file not found"):
            load_env("/nonexistent/path/.env.jira")

    def test_default_missing_file_returns_empty(self, tmp_path, monkeypatch):
        """Should return empty dict when default file doesn't exist."""
        # Point DEFAULT_ENV_FILE to a path that doesn't exist
        monkeypatch.setattr(
            "jira.lib.config.DEFAULT_ENV_FILE",
            tmp_path / "nonexistent_env_file",
        )
        # Clear any env vars that would be picked up
        for var in ["JIRA_URL", "JIRA_USERNAME", "JIRA_API_TOKEN",
                     "JIRA_PERSONAL_TOKEN", "JIRA_CLOUD"]:
            monkeypatch.delenv(var, raising=False)

        config = load_env()

        assert config == {}

    def test_env_vars_fill_missing_values(self, tmp_path, monkeypatch):
        """Should use environment variables for keys not in file."""
        env_file = tmp_path / ".env"
        env_file.write_text("JIRA_URL=https://test.atlassian.net\n")
        monkeypatch.setenv("JIRA_USERNAME", "env_user")

        config = load_env(str(env_file))

        assert config["JIRA_URL"] == "https://test.atlassian.net"
        assert config["JIRA_USERNAME"] == "env_user"

    def test_file_values_take_precedence_over_env(self, tmp_path, monkeypatch):
        """File values should win over environment variables."""
        env_file = tmp_path / ".env"
        env_file.write_text("JIRA_URL=https://from-file.atlassian.net\n")
        monkeypatch.setenv("JIRA_URL", "https://from-env.atlassian.net")

        config = load_env(str(env_file))

        assert config["JIRA_URL"] == "https://from-file.atlassian.net"


class TestValidateConfig:
    """Tests for validate_config()."""

    def test_missing_url_returns_error(self):
        """Should report missing JIRA_URL."""
        errors = validate_config({})

        assert any("JIRA_URL" in e for e in errors)

    def test_invalid_url_format_returns_error(self):
        """Should reject URLs not starting with http:// or https://."""
        config = {
            "JIRA_URL": "ftp://bad.example.com",
            "JIRA_PERSONAL_TOKEN": "token123",
        }

        errors = validate_config(config)

        assert any("must start with http://" in e for e in errors)

    def test_valid_cloud_config(self):
        """Should pass with URL + USERNAME + API_TOKEN."""
        config = {
            "JIRA_URL": "https://test.atlassian.net",
            "JIRA_USERNAME": "user@example.com",
            "JIRA_API_TOKEN": "secret",
        }

        errors = validate_config(config)

        assert errors == []

    def test_valid_pat_config(self):
        """Should pass with URL + PERSONAL_TOKEN."""
        config = {
            "JIRA_URL": "https://jira.example.com",
            "JIRA_PERSONAL_TOKEN": "pat-token",
        }

        errors = validate_config(config)

        assert errors == []

    def test_missing_all_auth_returns_error(self):
        """Should report missing credentials when no auth is provided."""
        config = {"JIRA_URL": "https://test.atlassian.net"}

        errors = validate_config(config)

        assert any("authentication" in e.lower() for e in errors)


class TestGetAuthMode:
    """Tests for get_auth_mode()."""

    def test_returns_pat_with_personal_token(self):
        """Should return 'pat' when JIRA_PERSONAL_TOKEN is set."""
        config = {"JIRA_PERSONAL_TOKEN": "token123"}

        assert get_auth_mode(config) == "pat"

    def test_returns_cloud_without_personal_token(self):
        """Should return 'cloud' when JIRA_PERSONAL_TOKEN is absent."""
        config = {"JIRA_USERNAME": "user", "JIRA_API_TOKEN": "secret"}

        assert get_auth_mode(config) == "cloud"
