"""Unit tests for Jira client initialization."""

from unittest.mock import patch, MagicMock

from jira.lib.client import get_jira_client


@patch("jira.lib.client.Jira")
@patch("jira.lib.client.load_env")
@patch("jira.lib.client.validate_config", return_value=[])
@patch("jira.lib.client.get_auth_mode", return_value="pat")
def test_pat_auth_passes_timeout(mock_auth_mode, mock_validate, mock_load_env, mock_jira_cls):
    """Verify timeout=30 is passed to Jira constructor for PAT auth."""
    mock_load_env.return_value = {
        "JIRA_URL": "https://jira.example.com",
        "JIRA_PERSONAL_TOKEN": "test-token",
        "JIRA_CLOUD": "false",
    }
    mock_jira_cls.return_value = MagicMock()

    get_jira_client()

    mock_jira_cls.assert_called_once_with(
        url="https://jira.example.com",
        token="test-token",
        cloud=False,
        timeout=30,
    )


@patch("jira.lib.client.Jira")
@patch("jira.lib.client.load_env")
@patch("jira.lib.client.validate_config", return_value=[])
@patch("jira.lib.client.get_auth_mode", return_value="cloud")
def test_cloud_auth_passes_timeout(mock_auth_mode, mock_validate, mock_load_env, mock_jira_cls):
    """Verify timeout=30 is passed to Jira constructor for cloud auth."""
    mock_load_env.return_value = {
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_USERNAME": "user@example.com",
        "JIRA_API_TOKEN": "api-token",
        "JIRA_CLOUD": "true",
    }
    mock_jira_cls.return_value = MagicMock()

    get_jira_client()

    mock_jira_cls.assert_called_once_with(
        url="https://test.atlassian.net",
        username="user@example.com",
        password="api-token",
        cloud=True,
        timeout=30,
    )
