"""Jira bridge plugin - issue tracking and workflow automation."""

from .formatters import register_jira_formatters
from .plugin import JiraPlugin

# Register formatters after imports
register_jira_formatters()

__all__ = ["JiraPlugin"]
