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
| `json` | Automation | Scripts | Raw API data |

## File Structure

```
formatters/
├── __init__.py      # Registry, exports, register_jira_formatters()
├── base.py          # Base classes, utilities, icons/styles
├── issue.py         # Single issue (with linked issues, warnings)
├── search.py        # Search results, bulk fetch results
├── transitions.py   # Workflow transitions
├── comments.py      # Issue comments
├── worklogs.py      # Time tracking worklogs
├── links.py         # Issue-to-issue links
├── linktypes.py     # Available link types
├── weblinks.py      # External web links
├── watchers.py      # Issue watchers
├── attachments.py   # File attachments
├── user.py          # User info
└── health.py        # Health check status
```

## Using Formatters

In a route handler:

```python
from ..response import formatted

@router.get("/issue/{key}")
async def get_issue(key: str, format: str = "json", client=Depends(jira)):
    issue = client.issue(key)
    return formatted(issue, format, "issue")
    #                │       │        │
    #                │       │        └─ Data type (registry key)
    #                │       └─ Format from --format param
    #                └─ Raw API data
```

## Format Examples

### Issue - AI Format (Default)

```
ISSUE: PROJ-123
type: Bug
status: In Progress
priority: High
summary: Fix login redirect after password reset
assignee: John Doe
description: Users are redirected to homepage instead of...
linked_issues: 2
  - blocks PROJ-124: [Open] Implement SSO
  - is blocked by PROJ-100: [Done] Auth refactor
WARNING: All requested fields returned None - check field names
```

### Issue - Rich Format

```
╭──────────────────────────────────────────────────────────╮
│ 🐛  PROJ-123  Bug                                        │
├──────────────────────────────────────────────────────────┤
│ Fix login redirect after password reset                  │
│                                                          │
│ Status    ► In Progress                                  │
│ Priority  ▲ High                                         │
│ Assignee  John Doe                                       │
│ Reporter  Jane Smith                                     │
╰──────────────────────────────────────────────────────────╯
```

### Issue - Markdown Format

```markdown
## PROJ-123: Fix login redirect after password reset

| Field | Value |
|-------|-------|
| Type | Bug |
| Status | In Progress |
| Priority | High |
| Assignee | John Doe |

### Description

Users are redirected to homepage instead of...
```

### Search Results - AI Format

```
FOUND: 15 issues
- PROJ-123: [In Progress] Fix login redirect after password reset
- PROJ-124: [Open] Implement SSO integration
- PROJ-125: [Done] Update user documentation
...
MISSING: PROJ-999, PROJ-888
WARNING: Issues not found: PROJ-999, PROJ-888
```

## v1.2.0 Features

### Linked Issues Display

When using `--include-links`, linked issues are shown:

```python
# AI format output includes:
linked_issues: 3
  - blocks PROJ-124: [Open] SSO implementation
  - is blocked by PROJ-100: [Done] Auth refactor
  - relates to PROJ-150: [In Progress] Security audit
```

### Field Validation Warnings

When requested fields return None, a warning is added:

```python
# Tool validates fields against KNOWN_FIELDS set
WARNING: Unknown fields (may be custom): customfield_10001, foobar
WARNING: All requested fields returned None - check field names
```

### Bulk Fetch Missing Issues

GetIssues reports which keys weren't found:

```python
# Response includes missing keys
FOUND: 18 issues
...
MISSING: PROJ-999, PROJ-888
WARNING: Issues not found: PROJ-999, PROJ-888
```

## Base Classes

### Formatter (base.py)

```python
class Formatter:
    """Base formatter with default implementations."""

    def format(self, data: Any) -> str:
        """Format data as string. Override in subclasses."""
        return str(data)

    def format_error(self, message: str, hint: str | None = None) -> str:
        """Format error message."""
        if hint:
            return f"Error: {message}\nHint: {hint}"
        return f"Error: {message}"
```

### AIFormatter

```python
class AIFormatter(Formatter):
    """Token-efficient format for AI consumption."""

    def format(self, data: Any) -> str:
        # Default: compact JSON
        return json.dumps(data, separators=(",", ":"), default=str)
```

### RichFormatter

```python
class RichFormatter(Formatter):
    """Rich terminal output with colors/tables."""

    def format(self, data: Any) -> str:
        # Default: pretty JSON
        return json.dumps(data, indent=2, default=str)
```

### MarkdownFormatter

```python
class MarkdownFormatter(Formatter):
    """Markdown table output."""

    def format(self, data: Any) -> str:
        # Default: JSON in code block
        return f"```json\n{json.dumps(data, indent=2)}\n```"
```

## Utility Functions

### render_to_string(renderable)

Convert Rich object to ANSI string:

```python
from .base import render_to_string, Table

table = Table()
table.add_row("Key", "PROJ-123")
output = render_to_string(table)  # Returns ANSI-colored string
```

### make_issue_link(key)

Create clickable terminal hyperlink:

```python
from .base import make_issue_link

link = make_issue_link("PROJ-123")
# Returns Rich Text with hyperlink to Jira issue
```

### Style Helpers

```python
from .base import get_status_style, get_priority_style, get_type_icon

get_type_icon("Bug")           # "🐛"
get_type_icon("Task")          # "☑️"
get_type_icon("Story")         # "📗"
get_type_icon("Epic")          # "⚡"

get_status_style("Done")       # ("✓", "green")
get_status_style("In Progress") # ("►", "yellow")
get_status_style("Blocked")    # ("✗", "red")

get_priority_style("High")     # ("▲", "yellow")
get_priority_style("Critical") # ("▲▲", "bold red")
```

## Registry

### Registration

```python
# In formatters/__init__.py

def register_jira_formatters():
    # Issue formatters
    formatter_registry.register("jira", "issue", "ai", JiraIssueAIFormatter())
    formatter_registry.register("jira", "issue", "rich", JiraIssueRichFormatter())
    formatter_registry.register("jira", "issue", "markdown", JiraIssueMarkdownFormatter())

    # Search formatters (also used for bulk fetch)
    formatter_registry.register("jira", "search", "ai", JiraSearchAIFormatter())
    # ...
```

### Lookup Rules

```python
# Exact match (when data_type specified)
formatter_registry.get("ai", plugin="jira", data_type="issue")
# Returns JiraIssueAIFormatter or None

# Plugin-wide fallback (when data_type=None)
formatter_registry.get("ai", plugin="jira")
# Returns first matching jira:*:ai formatter
```

**Important:** When `data_type` is specified, only exact matches are returned. This prevents returning the wrong formatter (e.g., issue formatter for user data).

## Adding a New Formatter

### 1. Create Formatter Class

```python
# formatters/sprints.py

from typing import Any
from .base import (
    AIFormatter, RichFormatter,
    Table, box, render_to_string
)

class JiraSprintsAIFormatter(AIFormatter):
    """AI-optimized sprint list formatting."""

    def format(self, data: Any) -> str:
        if not data:
            return "NO_SPRINTS"

        sprints = data if isinstance(data, list) else data.get("values", [])
        lines = [f"SPRINTS: {len(sprints)}"]

        for s in sprints:
            state = s.get("state", "?")
            name = s.get("name", "?")
            goal = (s.get("goal") or "")[:40]
            lines.append(f"- [{state}] {name}: {goal}")

        return "\n".join(lines)


class JiraSprintsRichFormatter(RichFormatter):
    """Rich terminal sprint formatting."""

    def format(self, data: Any) -> str:
        # ... Rich table implementation
```

### 2. Register in __init__.py

```python
# formatters/__init__.py

from .sprints import JiraSprintsAIFormatter, JiraSprintsRichFormatter

__all__ = [
    # ...existing...
    "JiraSprintsAIFormatter",
    "JiraSprintsRichFormatter",
]

def register_jira_formatters():
    # ...existing...
    formatter_registry.register("jira", "sprints", "ai", JiraSprintsAIFormatter())
    formatter_registry.register("jira", "sprints", "rich", JiraSprintsRichFormatter())
```

### 3. Use in Route

```python
# In route handler:
return formatted(data, format, "sprints")
#                              ^^^^^^^ Must match registry key
```

## Design Principles

1. **JSON format is default** - AI format recommended for LLM consumers
2. **Structured over pretty** - AI format uses consistent patterns
3. **Include context** - Warnings, linked issues, missing items
4. **Human format is optional** - Rich/markdown for human consumers
5. **JSON for scripts** - Raw data when programmatic access needed

## Testing Formats

```bash
# Compare all formats
jira issue PROJ-123 --format ai
jira issue PROJ-123 --format rich
jira issue PROJ-123 --format markdown
jira issue PROJ-123 --format json

# With linked issues
jira issue PROJ-123 --include-links --format ai
```
