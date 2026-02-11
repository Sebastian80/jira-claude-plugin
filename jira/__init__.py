"""Jira CLI - Standalone issue tracking and workflow automation."""

import importlib.metadata

# Importing formatters triggers decorator-based auto-registration
import jira.formatters  # noqa: F401

__version__ = importlib.metadata.version("jira-cli")
