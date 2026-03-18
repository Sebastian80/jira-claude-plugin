# Formatters

Transform Jira API responses into different output formats optimized for different consumers.

## Overview

```
                    Jira API Response (dict)
                              │
                              ▼
                    formatted(data, "ai", "issue")
                              │
                              ▼
                    FormatterRegistry lookup
                    key: "jira:issue:ai"
                              │
                              ▼
                    JiraIssueAIFormatter.format(data)
                              │
                              ▼
                    Token-efficient string output
```

## Available Formats

| Format | Purpose | Consumer | Characteristics |
|--------|---------|----------|-----------------|
| `ai` | LLM consumption | Claude, GPT | Token-efficient, structured, no decoration |
| `rich` | Human terminal | Developer | Colors, icons, panels, tables |
| `markdown` | Documentation | PRs, docs | Markdown tables, links |
| `json` | Automation | Scripts | Raw API data (bypasses formatters) |

## File Structure

```
formatters/
├── __init__.py      # Auto-registration imports + base re-exports
├── base.py          # Base classes, registry, utilities, icons/styles
├── issue.py         # Single issue
├── show.py          # Combined issue + comments view (reuses issue helpers)
├── search.py        # Search results
├── transitions.py   # Workflow transitions
├── comments.py      # Issue comments
├── worklogs.py      # Time tracking worklogs
├── links.py         # Issue-to-issue links
├── linktypes.py     # Available link types
├── weblinks.py      # External web links
├── watchers.py      # Issue watchers
├── attachments.py   # File attachments
├── boards.py        # Agile boards
├── projects.py      # Project listing
├── priorities.py    # Priority levels
├── statuses.py      # Status values
├── user.py          # User info
└── health.py        # Health check status
```

## Using Formatters

In a route handler:

```python
from ..response import formatted, OutputFormat, FORMAT_QUERY

@router.get("/issue/{key}")
def get_issue(key: str, format: OutputFormat = FORMAT_QUERY, client=Depends(jira)):
    issue = client.issue(key)
    return formatted(issue, format, "issue")
    #                │       │        │
    #                │       │        └─ Data type (registry key)
    #                │       └─ Format from --format param
    #                └─ Raw API data
```

## Base Classes

### Formatter (base.py)

```python
class Formatter:
    def format(self, data: Any) -> str: ...
    def format_error(self, message: str, hint: str | None = None) -> str: ...

class AIFormatter(Formatter):     # Compact JSON (separators=(",", ":"))
class RichFormatter(Formatter):   # Pretty JSON fallback
class MarkdownFormatter(Formatter): # JSON in code block fallback
```

Concrete formatters override `format()` to produce entity-specific output.

## Registry

### Registration

```python
@register_formatter("jira", "issue", "ai")
class JiraIssueAIFormatter(AIFormatter):
    def format(self, data: Any) -> str:
        ...
```

Registration happens automatically when the module is imported. Importing `jira.formatters` in `jira/__init__.py` triggers all decorator registrations.

### Lookup Rules

```python
# Exact match (when data_type specified)
formatter_registry.get("ai", plugin="jira", data_type="issue")
# Returns JiraIssueAIFormatter or None

# Plugin-wide fallback (when data_type=None)
formatter_registry.get("ai", plugin="jira")
# Returns first matching jira:*:ai formatter
```

When `data_type` is specified, only exact matches are returned — prevents returning the wrong formatter.

## Utility Functions

```python
from .base import render_to_string, make_issue_link
from .base import get_type_icon, get_status_style, get_priority_style

get_type_icon("Bug")            # "🐛"
get_status_style("Done")        # ("✓", "green")
get_priority_style("High")      # ("▲", "yellow")

make_issue_link("PROJ-123")     # Rich Text with clickable hyperlink
render_to_string(table)         # Rich object → ANSI string
```

## Adding a New Formatter

### 1. Create Formatter Class with Decorator

```python
# formatters/myentity.py
from .base import AIFormatter, RichFormatter, MarkdownFormatter, register_formatter

@register_formatter("jira", "myentity", "ai")
class MyEntityAIFormatter(AIFormatter):
    def format(self, data: Any) -> str:
        ...

@register_formatter("jira", "myentity", "rich")
class MyEntityRichFormatter(RichFormatter):
    def format(self, data: Any) -> str:
        ...

@register_formatter("jira", "myentity", "markdown")
class MyEntityMarkdownFormatter(MarkdownFormatter):
    def format(self, data: Any) -> str:
        ...
```

### 2. Import in \_\_init\_\_.py

```python
# formatters/__init__.py — add bare import to trigger registration
from . import myentity  # noqa: F401
```

### 3. Use in Route

```python
return formatted(data, format, "myentity")
#                              ^^^^^^^^^ Must match decorator's data_type
```
