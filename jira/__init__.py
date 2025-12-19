"""Jira CLI - Standalone issue tracking and workflow automation."""

from .formatters import register_jira_formatters

# Register formatters on import
register_jira_formatters()

__version__ = "2.0.0"
