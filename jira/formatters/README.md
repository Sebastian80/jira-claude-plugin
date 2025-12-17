# Formatters

Transform Jira API responses into different output formats.

## Overview

```
API Response (dict)
       │
       ▼
formatted(data, "ai", "issue")
       │
       ▼
FormatterRegistry lookup
       │
       ▼
JiraIssueAIFormatter.format(data)
       │
       ▼
Formatted string or ToolResult
```

## Available Formats

| Format | Purpose | Output |
|--------|---------|--------|
| `json` | Raw data | JSON string |
| `rich` | Terminal | Colored tables/panels (Rich library) |
| `ai` | AI context | Token-efficient structured text |
| `markdown` | Documentation | Markdown tables |

## Using Formatters

In a Tool's execute method:

```python
from ..response import formatted

async def execute(self, ctx: ToolContext) -> Any:
    issue = ctx.client.issue(self.key)
    return formatted(issue, self.format, "issue")
    #                │       │            │
    #                │       │            └─ entity type (registry key)
    #                │       └─ format name from CLI --format param
    #                └─ raw API data
```

The `formatted()` helper:
1. Looks up formatter in registry: `("jira", entity_type, format_name)`
2. Falls back to JSON if not found
3. Returns formatted output

## File Structure

```
formatters/
├── __init__.py      # Registry, exports, register_jira_formatters()
├── base.py          # Base classes, utilities, registry
├── issue.py         # JiraIssueRichFormatter, JiraIssueAIFormatter, ...
├── search.py        # JiraSearchRichFormatter, JiraSearchAIFormatter, ...
├── transitions.py   # JiraTransitionsRichFormatter, JiraTransitionsAIFormatter
├── comments.py      # JiraCommentsRichFormatter, JiraCommentsAIFormatter
├── worklogs.py      # JiraWorklogsRichFormatter, JiraWorklogsAIFormatter
├── links.py         # JiraLinksRichFormatter, JiraLinksAIFormatter
├── linktypes.py     # JiraLinkTypesRichFormatter, JiraLinkTypesAIFormatter
├── watchers.py      # JiraWatchersRichFormatter, JiraWatchersAIFormatter
├── attachments.py   # JiraAttachmentsRichFormatter, JiraAttachmentsAIFormatter
└── weblinks.py      # JiraWebLinksRichFormatter, JiraWebLinksAIFormatter
```

## Formatter Base Classes

### base.py

```python
class Formatter(ABC):
    """Abstract base for all formatters."""
    @abstractmethod
    def format(self, data: Any) -> str:
        pass

class JsonFormatter(Formatter):
    """JSON output - works for any data."""
    def format(self, data: Any) -> str:
        return json.dumps(data, indent=2, default=str)

class RichFormatter(Formatter):
    """Rich terminal output with colors/tables."""
    @abstractmethod
    def format(self, data: Any) -> str:
        pass

class AIFormatter(Formatter):
    """Token-efficient format for AI consumption."""
    @abstractmethod
    def format(self, data: Any) -> str:
        pass

class MarkdownFormatter(Formatter):
    """Markdown table output."""
    @abstractmethod
    def format(self, data: Any) -> str:
        pass
```

## Adding a New Formatter

### 1. Create formatter class

```python
# formatters/myentity.py

from .base import AIFormatter, RichFormatter, Table, Panel, render_to_string

class MyEntityRichFormatter(RichFormatter):
    """Rich terminal output for MyEntity."""

    def format(self, data: Any) -> str:
        if not data:
            return "No data"

        table = Table(title="My Entity")
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        table.add_row("Name", data.get("name", ""))
        table.add_row("Status", data.get("status", ""))

        return render_to_string(table)


class MyEntityAIFormatter(AIFormatter):
    """AI-friendly output for MyEntity."""

    def format(self, data: Any) -> str:
        if not data:
            return "No data"

        lines = [
            f"Name: {data.get('name', '')}",
            f"Status: {data.get('status', '')}",
        ]
        return "\n".join(lines)
```

### 2. Export in __init__.py

```python
# formatters/__init__.py

from .myentity import MyEntityAIFormatter, MyEntityRichFormatter

__all__ = [
    # ...existing...
    "MyEntityRichFormatter",
    "MyEntityAIFormatter",
]
```

### 3. Register in register_jira_formatters()

```python
# formatters/__init__.py

def register_jira_formatters():
    # ...existing...

    # MyEntity formatters
    formatter_registry.register("jira", "myentity", "rich", MyEntityRichFormatter())
    formatter_registry.register("jira", "myentity", "ai", MyEntityAIFormatter())
```

### 4. Use in Tool

```python
# tools/myentity.py

async def execute(self, ctx: ToolContext) -> Any:
    data = ctx.client.get_myentity(self.key)
    return formatted(data, self.format, "myentity")
    #                                    └─ matches registry key
```

## Registry

The `FormatterRegistry` stores formatters by (plugin, entity, format):

```python
formatter_registry.register("jira", "issue", "ai", JiraIssueAIFormatter())
#                            │       │        │     │
#                            │       │        │     └─ formatter instance
#                            │       │        └─ format name
#                            │       └─ entity type
#                            └─ plugin name

# Lookup
formatter = formatter_registry.get("jira", "issue", "ai")
output = formatter.format(data)
```

## Utility Functions (base.py)

### render_to_string(renderable)

Convert Rich object to string for CLI output:

```python
from .base import render_to_string, Table

table = Table()
table.add_row("foo", "bar")
output = render_to_string(table)  # Returns ANSI-colored string
```

### make_issue_link(key, base_url)

Generate clickable issue URL:

```python
url = make_issue_link("PROJ-123", "https://jira.example.com")
# Returns: "https://jira.example.com/browse/PROJ-123"
```

### Style helpers

```python
from .base import get_status_style, get_priority_style, get_type_icon

get_status_style("Done")      # Returns: "green"
get_status_style("In Progress")  # Returns: "yellow"
get_priority_style("High")    # Returns: "red"
get_type_icon("Bug")          # Returns: "🐛"
get_type_icon("Task")         # Returns: "✓"
```

## Format Examples

### Issue - JSON

```json
{
  "key": "PROJ-123",
  "fields": {
    "summary": "Fix login bug",
    "status": {"name": "In Progress"},
    "assignee": {"displayName": "John"}
  }
}
```

### Issue - Rich

```
╭─────────────────────────────────────────╮
│ 🐛 PROJ-123: Fix login bug              │
├─────────────────────────────────────────┤
│ Status:   In Progress                   │
│ Assignee: John                          │
│ Priority: High                          │
╰─────────────────────────────────────────╯
```

### Issue - AI

```
PROJ-123: Fix login bug
Type: Bug | Status: In Progress | Priority: High
Assignee: John
Created: 2024-01-15 | Updated: 2024-01-16

Description:
Users cannot log in after password reset...
```

### Issue - Markdown

```markdown
| Field | Value |
|-------|-------|
| Key | PROJ-123 |
| Summary | Fix login bug |
| Status | In Progress |
| Assignee | John |
```

## Design Principles

1. **AI format is default** - Token-efficient, structured, no decoration
2. **Rich for humans** - Colors, panels, tables for terminal
3. **JSON for scripts** - Raw data, no transformation
4. **Markdown for docs** - Tables that render in docs/PRs

## Testing

```bash
# Test different formats
jira issue PROJ-123 --format json
jira issue PROJ-123 --format rich
jira issue PROJ-123 --format ai
jira issue PROJ-123 --format markdown
```
