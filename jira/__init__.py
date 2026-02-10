"""Jira CLI - Standalone issue tracking and workflow automation."""

import importlib.metadata

from .formatters import register_jira_formatters

# Register formatters on import
register_jira_formatters()

__version__ = importlib.metadata.version("jira-cli")
