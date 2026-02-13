"""Jira client initialization for CLI scripts."""

import mimetypes
import os
from typing import BinaryIO, Optional

from atlassian import Jira

from .config import load_env, validate_config, get_auth_mode


class JiraClient(Jira):
    """Jira client with fixed multipart attachment uploads.

    urllib3 2.x no longer auto-sets per-part Content-Type in multipart forms
    when using the simple ``files={"file": fobj}`` form. This override uses
    the explicit tuple form so Jira receives the correct MIME type.
    """

    def add_attachment_object(self, issue_key: str, attachment: BinaryIO):
        name = getattr(attachment, "name", None) or "attachment"
        basename = os.path.basename(name)
        content_type = mimetypes.guess_type(basename)[0] or "application/octet-stream"
        base_url = self.resource_url("issue")
        url = f"{base_url}/{issue_key}/attachments"
        files = {"file": (basename, attachment, content_type)}
        return self.post(url, headers=self.no_check_headers, files=files)

def get_jira_client(env_file: Optional[str] = None) -> Jira:
    """Initialize and return a Jira client.

    Supports two authentication modes:
    - Cloud: JIRA_USERNAME + JIRA_API_TOKEN
    - Server/DC: JIRA_PERSONAL_TOKEN (Personal Access Token)

    Args:
        env_file: Optional path to environment file

    Returns:
        Configured Jira client instance

    Raises:
        FileNotFoundError: If env file doesn't exist
        ValueError: If configuration is invalid
        ConnectionError: If cannot connect to Jira
    """
    config = load_env(env_file)

    errors = validate_config(config)
    if errors:
        raise ValueError("Configuration errors:\n  " + "\n  ".join(errors))

    url = config['JIRA_URL']
    auth_mode = get_auth_mode(config)

    # Determine if Cloud or Server/DC
    is_cloud = config.get('JIRA_CLOUD', '').lower() == 'true'

    # Auto-detect if not specified
    if 'JIRA_CLOUD' not in config:
        is_cloud = '.atlassian.net' in url.lower()

    try:
        if auth_mode == 'pat':
            # Server/DC with Personal Access Token
            client = JiraClient(
                url=url,
                token=config['JIRA_PERSONAL_TOKEN'],
                cloud=is_cloud,
                timeout=30,
            )
        else:
            # Cloud with username + API token
            client = JiraClient(
                url=url,
                username=config['JIRA_USERNAME'],
                password=config['JIRA_API_TOKEN'],
                cloud=is_cloud,
                timeout=30,
            )
        return client
    except Exception as e:
        if auth_mode == 'pat':
            raise ConnectionError(
                f"Failed to connect to Jira at {url}\n\n"
                f"  Error: {e}\n\n"
                f"  Please verify:\n"
                f"    - JIRA_URL is correct\n"
                f"    - JIRA_PERSONAL_TOKEN is a valid Personal Access Token\n"
            )
        else:
            raise ConnectionError(
                f"Failed to connect to Jira at {url}\n\n"
                f"  Error: {e}\n\n"
                f"  Please verify:\n"
                f"    - JIRA_URL is correct\n"
                f"    - JIRA_USERNAME is your email (Cloud) or username (Server/DC)\n"
                f"    - JIRA_API_TOKEN is valid\n"
            )
