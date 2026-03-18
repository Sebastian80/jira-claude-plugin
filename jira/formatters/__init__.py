"""
Jira formatters package.

Provides Rich, AI, and Markdown formatters for all Jira data types.
Importing this package triggers decorator-based auto-registration.
"""

# Import all formatter modules to trigger @register_formatter decorators
from . import (  # noqa: F401
    attachments,
    boards,
    comments,
    health,
    issue,
    links,
    linktypes,
    priorities,
    projects,
    search,
    show,
    statuses,
    transitions,
    user,
    watchers,
    weblinks,
    worklogs,
)

# Re-export base classes and utilities used by external code
from .base import (
    AIFormatter,
    Formatter,
    FormatterRegistry,
    JsonFormatter,
    MarkdownFormatter,
    Panel,
    RichFormatter,
    Table,
    Text,
    box,
    convert_jira_markup,
    formatter_registry,
    get_priority_style,
    get_status_style,
    get_type_icon,
    make_issue_link,
    render_to_string,
)
