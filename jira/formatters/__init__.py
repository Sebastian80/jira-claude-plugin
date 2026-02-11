"""
Jira formatters package.

Provides Rich, AI, and Markdown formatters for all Jira data types.
Formatters are plugin-local (not imported from bridge).
"""

from .attachments import JiraAttachmentsAIFormatter, JiraAttachmentsRichFormatter
from .boards import JiraBoardsAIFormatter, JiraBoardsMarkdownFormatter, JiraBoardsRichFormatter
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
from .comments import JiraCommentsAIFormatter, JiraCommentsMarkdownFormatter, JiraCommentsRichFormatter
from .priorities import JiraPrioritiesAIFormatter, JiraPrioritiesMarkdownFormatter, JiraPrioritiesRichFormatter
from .projects import (
    JiraProjectAIFormatter,
    JiraProjectMarkdownFormatter,
    JiraProjectRichFormatter,
    JiraProjectsAIFormatter,
    JiraProjectsMarkdownFormatter,
    JiraProjectsRichFormatter,
)
from .statuses import JiraStatusesAIFormatter, JiraStatusesMarkdownFormatter, JiraStatusesRichFormatter
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
from .show import JiraShowAIFormatter, JiraShowMarkdownFormatter, JiraShowRichFormatter

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
    "JiraCommentsMarkdownFormatter",
    # Statuses formatters
    "JiraStatusesRichFormatter",
    "JiraStatusesAIFormatter",
    "JiraStatusesMarkdownFormatter",
    # Priorities formatters
    "JiraPrioritiesRichFormatter",
    "JiraPrioritiesAIFormatter",
    "JiraPrioritiesMarkdownFormatter",
    # Link types formatters
    "JiraLinkTypesRichFormatter",
    "JiraLinkTypesAIFormatter",
    # Issue links formatters
    "JiraLinksRichFormatter",
    "JiraLinksAIFormatter",
    # Watchers formatters
    "JiraWatchersRichFormatter",
    "JiraWatchersAIFormatter",
    # Boards formatters
    "JiraBoardsRichFormatter",
    "JiraBoardsAIFormatter",
    "JiraBoardsMarkdownFormatter",
    # Projects formatters
    "JiraProjectsRichFormatter",
    "JiraProjectsAIFormatter",
    "JiraProjectsMarkdownFormatter",
    "JiraProjectRichFormatter",
    "JiraProjectAIFormatter",
    "JiraProjectMarkdownFormatter",
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
    # Show (combined issue+comments) formatters
    "JiraShowRichFormatter",
    "JiraShowAIFormatter",
    "JiraShowMarkdownFormatter",
]
