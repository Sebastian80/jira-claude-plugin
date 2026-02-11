"""Unit tests for Jira client initialization.

Tests the full get_jira_client() flow with real config parsing/validation,
only mocking the Jira class itself (external dependency).
"""

from unittest.mock import patch, MagicMock

import pytest

from jira.lib.client import get_jira_client


@pytest.fixture
def pat_env_file(tmp_path):
    """Create an env file with PAT (Server/DC) authentication."""
    env_file = tmp_path / ".env.jira"
    env_file.write_text(
        "JIRA_URL=https://jira.example.com\n"
        "JIRA_PERSONAL_TOKEN=test-token\n"
        "JIRA_CLOUD=false\n"
    )
    return str(env_file)


@pytest.fixture
def cloud_env_file(tmp_path):
    """Create an env file with Cloud authentication."""
    env_file = tmp_path / ".env.jira"
    env_file.write_text(
        "JIRA_URL=https://test.atlassian.net\n"
        "JIRA_USERNAME=user@example.com\n"
        "JIRA_API_TOKEN=api-token\n"
        "JIRA_CLOUD=true\n"
    )
    return str(env_file)


@patch("jira.lib.client.Jira")
def test_pat_auth_passes_timeout(mock_jira_cls, pat_env_file):
    """Verify timeout=30 is passed to Jira constructor for PAT auth."""
    mock_jira_cls.return_value = MagicMock()

    get_jira_client(env_file=pat_env_file)

    mock_jira_cls.assert_called_once_with(
        url="https://jira.example.com",
        token="test-token",
        cloud=False,
        timeout=30,
    )


@patch("jira.lib.client.Jira")
def test_cloud_auth_passes_timeout(mock_jira_cls, cloud_env_file):
    """Verify timeout=30 is passed to Jira constructor for cloud auth."""
    mock_jira_cls.return_value = MagicMock()

    get_jira_client(env_file=cloud_env_file)

    mock_jira_cls.assert_called_once_with(
        url="https://test.atlassian.net",
        username="user@example.com",
        password="api-token",
        cloud=True,
        timeout=30,
    )


@patch("jira.lib.client.Jira")
def test_pat_auth_from_env_vars(mock_jira_cls, tmp_path, monkeypatch):
    """PAT config via environment variables should work without a file."""
    monkeypatch.setattr("jira.lib.config.DEFAULT_ENV_FILE", tmp_path / "nonexistent")
    monkeypatch.setenv("JIRA_URL", "https://jira.corp.com")
    monkeypatch.setenv("JIRA_PERSONAL_TOKEN", "env-pat-token")
    mock_jira_cls.return_value = MagicMock()

    get_jira_client()

    mock_jira_cls.assert_called_once_with(
        url="https://jira.corp.com",
        token="env-pat-token",
        cloud=False,
        timeout=30,
    )


@patch("jira.lib.client.Jira")
def test_cloud_auto_detected_from_atlassian_url(mock_jira_cls, tmp_path):
    """JIRA_CLOUD should be auto-detected when URL contains .atlassian.net."""
    env_file = tmp_path / ".env.jira"
    env_file.write_text(
        "JIRA_URL=https://myorg.atlassian.net\n"
        "JIRA_USERNAME=user@example.com\n"
        "JIRA_API_TOKEN=api-token\n"
    )
    mock_jira_cls.return_value = MagicMock()

    get_jira_client(env_file=str(env_file))

    mock_jira_cls.assert_called_once_with(
        url="https://myorg.atlassian.net",
        username="user@example.com",
        password="api-token",
        cloud=True,
        timeout=30,
    )


@patch("jira.lib.client.Jira")
def test_non_atlassian_url_defaults_to_not_cloud(mock_jira_cls, tmp_path):
    """Without JIRA_CLOUD, non-atlassian URLs should default to cloud=False."""
    env_file = tmp_path / ".env.jira"
    env_file.write_text(
        "JIRA_URL=https://jira.mycompany.com\n"
        "JIRA_PERSONAL_TOKEN=my-pat\n"
    )
    mock_jira_cls.return_value = MagicMock()

    get_jira_client(env_file=str(env_file))

    mock_jira_cls.assert_called_once_with(
        url="https://jira.mycompany.com",
        token="my-pat",
        cloud=False,
        timeout=30,
    )


@patch("jira.lib.client.Jira")
def test_explicit_cloud_overrides_url_detection(mock_jira_cls, tmp_path):
    """JIRA_CLOUD=true should force cloud mode even for non-atlassian URLs."""
    env_file = tmp_path / ".env.jira"
    env_file.write_text(
        "JIRA_URL=https://jira.mycompany.com\n"
        "JIRA_PERSONAL_TOKEN=my-pat\n"
        "JIRA_CLOUD=true\n"
    )
    mock_jira_cls.return_value = MagicMock()

    get_jira_client(env_file=str(env_file))

    mock_jira_cls.assert_called_once_with(
        url="https://jira.mycompany.com",
        token="my-pat",
        cloud=True,
        timeout=30,
    )


def test_missing_url_raises_value_error(tmp_path):
    """Should raise ValueError when JIRA_URL is missing."""
    env_file = tmp_path / ".env.jira"
    env_file.write_text("JIRA_PERSONAL_TOKEN=token\n")

    with pytest.raises(ValueError, match="JIRA_URL"):
        get_jira_client(env_file=str(env_file))


def test_missing_auth_raises_value_error(tmp_path):
    """Should raise ValueError when no authentication credentials are provided."""
    env_file = tmp_path / ".env.jira"
    env_file.write_text("JIRA_URL=https://jira.example.com\n")

    with pytest.raises(ValueError, match="authentication"):
        get_jira_client(env_file=str(env_file))


def test_invalid_url_raises_value_error(tmp_path):
    """Should raise ValueError for URLs not starting with http(s)://."""
    env_file = tmp_path / ".env.jira"
    env_file.write_text(
        "JIRA_URL=ftp://bad.example.com\n"
        "JIRA_PERSONAL_TOKEN=token\n"
    )

    with pytest.raises(ValueError, match="must start with http"):
        get_jira_client(env_file=str(env_file))


def test_explicit_missing_file_raises_file_not_found():
    """Should raise FileNotFoundError when explicit env file doesn't exist."""
    with pytest.raises(FileNotFoundError, match="Environment file not found"):
        get_jira_client(env_file="/nonexistent/path/.env.jira")


@patch("jira.lib.client.Jira")
def test_jira_connection_error_wraps_as_connection_error_pat(mock_jira_cls, pat_env_file):
    """Connection failures should be wrapped as ConnectionError with PAT context."""
    mock_jira_cls.side_effect = Exception("Connection refused")

    with pytest.raises(ConnectionError, match="JIRA_PERSONAL_TOKEN"):
        get_jira_client(env_file=pat_env_file)


@patch("jira.lib.client.Jira")
def test_jira_connection_error_wraps_as_connection_error_cloud(mock_jira_cls, cloud_env_file):
    """Connection failures should be wrapped as ConnectionError with cloud context."""
    mock_jira_cls.side_effect = Exception("Connection refused")

    with pytest.raises(ConnectionError, match="JIRA_USERNAME"):
        get_jira_client(env_file=cloud_env_file)


@patch("jira.lib.client.Jira")
def test_returns_jira_client_instance(mock_jira_cls, pat_env_file):
    """Should return the Jira client instance on success."""
    sentinel = MagicMock()
    mock_jira_cls.return_value = sentinel

    result = get_jira_client(env_file=pat_env_file)

    assert result is sentinel
