# Extending the Jira Plugin

Step-by-step guide to adding new functionality to the standalone Jira plugin.

## Quick Reference

| Extension Type | Files to Modify | Complexity |
|----------------|-----------------|------------|
| New Route (endpoint) | `routes/<category>.py`, `routes/__init__.py` | Low |
| New Formatter | `formatters/<entity>.py`, `formatters/__init__.py` | Low |
| New Entity (full) | Routes + Formatters + Tests + Docs | Medium |
| New CLI command | `bin/jira` (usually nothing needed) | Low |

## Adding a New Route

Routes are FastAPI endpoint handlers. Each route module handles a related group of endpoints.

### Step 1: Create the Route Handler

```python
# routes/labels.py

from fastapi import APIRouter, Depends, Query

from ..deps import jira
from ..response import formatted, jira_error_handler, OutputFormat, FORMAT_QUERY

router = APIRouter()


@router.get("/labels/{key}")
@jira_error_handler(not_found="Issue {key} not found")
def get_labels(
    key: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """Get labels for an issue."""
    issue = client.issue(key, fields="labels")
    labels = issue.get("fields", {}).get("labels", [])
    return formatted(labels, format, "labels")
```

**Note:** Use sync `def`, not `async def`. The Jira client library is synchronous — FastAPI runs sync handlers in a threadpool automatically.

### Step 2: Register in routes/__init__.py

```python
# routes/__init__.py

from .labels import router as labels_router  # Add import

def create_router() -> APIRouter:
    router = APIRouter()
    # ...existing routes...
    router.include_router(labels_router)  # Add router
    return router
```

### Step 3: Done!

The route is now available via the CLI:
```bash
jira labels PROJ-123                    # GET /jira/labels/PROJ-123
jira labels PROJ-123 --format ai        # GET /jira/labels/PROJ-123?format=ai
```

## Route Patterns

### Pattern: GET with Formatting

```python
@router.get("/entity/{key}")
@jira_error_handler(not_found="Entity {key} not found")
def get_entity(
    key: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    data = client.get_entity(key)
    return formatted(data, format, "entity")
```

### Pattern: POST with Pydantic Body

```python
from pydantic import BaseModel

class CreateEntityBody(BaseModel):
    name: str
    project: str
    description: str | None = None

@router.post("/entity")
@jira_error_handler()
def create_entity(body: CreateEntityBody, client=Depends(jira)):
    result = client.create_entity(name=body.name, project=body.project)
    return success(result)
```

## Adding a New Formatter

### Step 1: Create Formatter Classes

```python
# formatters/labels.py

from typing import Any
from .base import AIFormatter, RichFormatter, MarkdownFormatter, register_formatter

@register_formatter("jira", "labels", "ai")
class JiraLabelsAIFormatter(AIFormatter):
    def format(self, data: Any) -> str:
        if not isinstance(data, list):
            return super().format(data)
        return f"labels: {', '.join(data)}" if data else "labels: none"

@register_formatter("jira", "labels", "rich")
class JiraLabelsRichFormatter(RichFormatter):
    def format(self, data: Any) -> str:
        ...

@register_formatter("jira", "labels", "markdown")
class JiraLabelsMarkdownFormatter(MarkdownFormatter):
    def format(self, data: Any) -> str:
        ...
```

### Step 2: Import in \_\_init\_\_.py

```python
# formatters/__init__.py — add bare import
from . import labels  # noqa: F401
```

The import triggers auto-registration via the `@register_formatter` decorator.

### Step 3: Use in Route

```python
return formatted(data, format, "labels")
#                              ^^^^^^^^ Must match decorator's data_type
```

## Testing Your Changes

```bash
# Run all tests
uv run pytest tests/ -v

# Specific file
uv run pytest tests/routes/test_labels.py -v

# Restart server to pick up changes
jira restart

# Manual testing
jira labels PROJ-123 --format ai
jira labels PROJ-123 --format rich
jira labels PROJ-123 --format json
```

## Common Gotchas

### Formatter Not Found

**Symptom:** Returns JSON instead of formatted output.

**Fix:** Ensure the `data_type` in `@register_formatter` matches the `data_type` in `formatted()`:
```python
@register_formatter("jira", "labels", "ai")  # ← "labels"
return formatted(data, format, "labels")       # ← must match
```

### Route Not Responding

**Symptom:** 404 errors from the CLI.

**Fix:**
1. Check you imported and included the router in `routes/__init__.py`
2. Restart the server: `jira restart`
3. Verify with `jira help` — your endpoint should appear

### Server Not Picking Up Changes

```bash
jira restart
```

## Jira API Reference

The `client` parameter is a `JiraClient` instance (subclass of `atlassian.Jira`). Documentation:
- https://atlassian-python-api.readthedocs.io/jira.html

Common methods:
```python
client.issue(key)                          # Get issue
client.issue(key, fields="summary,status") # Specific fields only
client.create_issue(fields={...})          # Create issue
client.update_issue_field(key, fields)     # Update fields
client.jql(query, limit=50)               # JQL search
client.issue_add_comment(key, body)        # Add comment
client.get_issue_transitions(key)          # List transitions
client.set_issue_status(key, status_name)  # Execute transition
client.projects()                          # List projects
client.project(key)                        # Get project
```

## Checklist for New Features

- [ ] Route handler with `@jira_error_handler`, `OutputFormat`, `Depends(jira)`
- [ ] Added to `routes/__init__.py`
- [ ] Formatter classes (AI, Rich, Markdown) with `@register_formatter`
- [ ] Imported in `formatters/__init__.py`
- [ ] Route tests in `tests/routes/`
- [ ] Mock client methods in `tests/mock_jira.py`
- [ ] Documentation in `skills/jira/references/commands.md`
- [ ] Server restart and manual testing with all formats
