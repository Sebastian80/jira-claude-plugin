"""
Jira formatters package.

Provides Rich, AI, and Markdown formatters for all Jira data types.
Formatters are plugin-local (not imported from bridge).
"""

from .attachments import JiraAttachmentsAIFormatter, JiraAttachmentsRichFormatter
from .health import (
    JiraHealthAIFormatter,
    JiraHealthMarkdownFormatter,
    JiraHealthRichFormatter,
)
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
    formatter_registry,
    get_priority_style,
    get_status_style,
    get_type_icon,
    make_issue_link,
    render_to_string,
)
from .comments import JiraCommentsAIFormatter, JiraCommentsRichFormatter
from .issue import (
    JiraIssueAIFormatter,
    JiraIssueMarkdownFormatter,
    JiraIssueRichFormatter,
)
from .links import JiraLinksAIFormatter, JiraLinksRichFormatter
from .linktypes import JiraLinkTypesAIFormatter, JiraLinkTypesRichFormatter
from .search import (
    JiraSearchAIFormatter,
    JiraSearchMarkdownFormatter,
    JiraSearchRichFormatter,
)
from .transitions import JiraTransitionsAIFormatter, JiraTransitionsRichFormatter
from .user import (
    JiraUserAIFormatter,
    JiraUserMarkdownFormatter,
    JiraUserRichFormatter,
)
from .watchers import JiraWatchersAIFormatter, JiraWatchersRichFormatter
from .weblinks import JiraWebLinksAIFormatter, JiraWebLinksRichFormatter
from .worklogs import JiraWorklogsAIFormatter, JiraWorklogsRichFormatter

__all__ = [
    # Base classes
    "Formatter",
    "JsonFormatter",
    "RichFormatter",
    "AIFormatter",
    "MarkdownFormatter",
    # Registry
    "FormatterRegistry",
    "formatter_registry",
    # Utilities
    "render_to_string",
    "make_issue_link",
    "get_type_icon",
    "get_status_style",
    "get_priority_style",
    # Rich re-exports
    "Table",
    "Panel",
    "Text",
    "box",
    # Issue formatters
    "JiraIssueRichFormatter",
    "JiraIssueAIFormatter",
    "JiraIssueMarkdownFormatter",
    # Search formatters
    "JiraSearchRichFormatter",
    "JiraSearchAIFormatter",
    "JiraSearchMarkdownFormatter",
    # Transitions formatters
    "JiraTransitionsRichFormatter",
    "JiraTransitionsAIFormatter",
    # Comments formatters
    "JiraCommentsRichFormatter",
    "JiraCommentsAIFormatter",
    # Link types formatters
    "JiraLinkTypesRichFormatter",
    "JiraLinkTypesAIFormatter",
    # Issue links formatters
    "JiraLinksRichFormatter",
    "JiraLinksAIFormatter",
    # Watchers formatters
    "JiraWatchersRichFormatter",
    "JiraWatchersAIFormatter",
    # Attachments formatters
    "JiraAttachmentsRichFormatter",
    "JiraAttachmentsAIFormatter",
    # Web links formatters
    "JiraWebLinksRichFormatter",
    "JiraWebLinksAIFormatter",
    # Worklogs formatters
    "JiraWorklogsRichFormatter",
    "JiraWorklogsAIFormatter",
    # User formatters
    "JiraUserRichFormatter",
    "JiraUserAIFormatter",
    "JiraUserMarkdownFormatter",
    # Health formatters
    "JiraHealthRichFormatter",
    "JiraHealthAIFormatter",
    "JiraHealthMarkdownFormatter",
    # Registration function
    "register_jira_formatters",
]


def register_jira_formatters():
    """Register all Jira formatters with the registry."""
    # Issue formatters
    formatter_registry.register("jira", "issue", "rich", JiraIssueRichFormatter())
    formatter_registry.register("jira", "issue", "ai", JiraIssueAIFormatter())
    formatter_registry.register("jira", "issue", "markdown", JiraIssueMarkdownFormatter())

    # Search formatters
    formatter_registry.register("jira", "search", "rich", JiraSearchRichFormatter())
    formatter_registry.register("jira", "search", "ai", JiraSearchAIFormatter())
    formatter_registry.register("jira", "search", "markdown", JiraSearchMarkdownFormatter())

    # Transitions formatters
    formatter_registry.register("jira", "transitions", "rich", JiraTransitionsRichFormatter())
    formatter_registry.register("jira", "transitions", "ai", JiraTransitionsAIFormatter())

    # Comments formatters
    formatter_registry.register("jira", "comments", "rich", JiraCommentsRichFormatter())
    formatter_registry.register("jira", "comments", "ai", JiraCommentsAIFormatter())

    # Link types formatters
    formatter_registry.register("jira", "linktypes", "rich", JiraLinkTypesRichFormatter())
    formatter_registry.register("jira", "linktypes", "ai", JiraLinkTypesAIFormatter())

    # Issue links formatters
    formatter_registry.register("jira", "links", "rich", JiraLinksRichFormatter())
    formatter_registry.register("jira", "links", "ai", JiraLinksAIFormatter())

    # Watchers formatters
    formatter_registry.register("jira", "watchers", "rich", JiraWatchersRichFormatter())
    formatter_registry.register("jira", "watchers", "ai", JiraWatchersAIFormatter())

    # Attachments formatters
    formatter_registry.register("jira", "attachments", "rich", JiraAttachmentsRichFormatter())
    formatter_registry.register("jira", "attachments", "ai", JiraAttachmentsAIFormatter())

    # Web links formatters
    formatter_registry.register("jira", "weblinks", "rich", JiraWebLinksRichFormatter())
    formatter_registry.register("jira", "weblinks", "ai", JiraWebLinksAIFormatter())

    # Worklogs formatters
    formatter_registry.register("jira", "worklogs", "rich", JiraWorklogsRichFormatter())
    formatter_registry.register("jira", "worklogs", "ai", JiraWorklogsAIFormatter())

    # User formatters
    formatter_registry.register("jira", "user", "rich", JiraUserRichFormatter())
    formatter_registry.register("jira", "user", "ai", JiraUserAIFormatter())
    formatter_registry.register("jira", "user", "markdown", JiraUserMarkdownFormatter())

    # Health formatters
    formatter_registry.register("jira", "health", "rich", JiraHealthRichFormatter())
    formatter_registry.register("jira", "health", "ai", JiraHealthAIFormatter())
    formatter_registry.register("jira", "health", "markdown", JiraHealthMarkdownFormatter())
