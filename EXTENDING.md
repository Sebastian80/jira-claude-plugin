# Extending the Jira Plugin

Step-by-step guide to adding new functionality to the standalone Jira plugin.

## Quick Reference

| Extension Type | Files to Modify | Complexity |
|----------------|-----------------|------------|
| New Route (endpoint) | `routes/<category>.py`, `routes/__init__.py` | Low |
| New Formatter | `formatters/<entity>.py`, `formatters/__init__.py` | Low |
| New Entity (full) | Routes + Formatters + Tests + Docs | Medium |
| New CLI command | `bin/jira` | Low |

## Adding a New Route

Routes are FastAPI endpoint handlers. Each route module handles a related group of endpoints.

### Step 1: Create the Route Handler

```python
# routes/sprints.py

from fastapi import APIRouter, Depends, Query, HTTPException

from ..deps import jira
from ..response import formatted, formatted_error

router = APIRouter()


@router.get("/sprints/{board_id}")
async def get_sprints(
    board_id: str,
    state: str = Query("active", description="Sprint state: active, closed, future"),
    format: str = Query("json", description="Output format: json, ai, rich, markdown"),
    client=Depends(jira),
):
    """Get sprints for an agile board.

    Lists all sprints for the specified board, filtered by state.
    """
    try:
        sprints = client.get_all_sprints_from_board(board_id, state=state)
        return formatted(sprints, format, "sprints")
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            return formatted_error(f"Board {board_id} not found", fmt=format, status=404)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sprint/{sprint_id}")
async def get_sprint(
    sprint_id: str,
    format: str = Query("json", description="Output format"),
    client=Depends(jira),
):
    """Get sprint details by ID."""
    try:
        sprint = client.get_sprint(sprint_id)
        return formatted(sprint, format, "sprint")
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            return formatted_error(f"Sprint {sprint_id} not found", fmt=format, status=404)
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 2: Register in routes/__init__.py

```python
# routes/__init__.py

from .sprints import router as sprints_router  # Add import

def create_router() -> APIRouter:
    router = APIRouter()

    # ...existing routes...
    router.include_router(sprints_router)  # Add router

    return router
```

### Step 3: Done!

The route is now available:
```bash
jira sprints 123                    # GET /jira/sprints/123
jira sprints 123 --state closed     # GET /jira/sprints/123?state=closed
jira sprint 456                     # GET /jira/sprint/456
```

## Route Patterns

### Pattern: GET with Formatting

```python
@router.get("/entity/{key}")
async def get_entity(
    key: str,
    format: str = Query("json", description="Output format"),
    client=Depends(jira),
):
    """Get entity by key."""
    try:
        data = client.get_entity(key)
        return formatted(data, format, "entity")
    except Exception as e:
        if "not found" in str(e).lower():
            return formatted_error(f"Entity {key} not found", fmt=format, status=404)
        raise HTTPException(status_code=500, detail=str(e))
```

### Pattern: POST with Validation

```python
@router.post("/entity")
async def create_entity(
    name: str = Query(..., description="Entity name"),
    project: str = Query(..., description="Project key"),
    client=Depends(jira),
):
    """Create a new entity."""
    try:
        result = client.create_entity(name=name, project=project)
        return success(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Pattern: Operation with Available Options

```python
@router.post("/do/{key}")
async def do_something(
    key: str,
    action: str = Query(..., description="Action to perform"),
    client=Depends(jira),
):
    """Perform an action on entity."""
    # Get available actions
    available = client.get_available_actions(key)
    action_names = [a["name"] for a in available]

    # Find matching action
    match = next((a for a in available if a["name"].lower() == action.lower()), None)

    if not match:
        return error(
            f"Action '{action}' not available",
            hint=f"Available: {', '.join(action_names)}"
        )

    # Perform action
    client.perform_action(key, match["id"])
    return success({"key": key, "action": action})
```

## Adding a New Formatter

Formatters transform API data into output formats.

### Step 1: Create Formatter Classes

```python
# formatters/sprints.py

from typing import Any
from .base import (
    AIFormatter, RichFormatter, MarkdownFormatter,
    Table, Panel, Text, box, render_to_string
)

class JiraSprintsAIFormatter(AIFormatter):
    """AI-optimized sprint formatting."""

    def format(self, data: Any) -> str:
        if not data:
            return "NO_SPRINTS"

        sprints = data if isinstance(data, list) else data.get("values", [])
        lines = [f"SPRINTS: {len(sprints)}"]

        for s in sprints:
            state = s.get("state", "?")
            name = s.get("name", "?")
            goal = s.get("goal", "")[:50] if s.get("goal") else ""
            lines.append(f"- [{state}] {name}: {goal}")

        return "\n".join(lines)


class JiraSprintsRichFormatter(RichFormatter):
    """Rich terminal sprint formatting."""

    def format(self, data: Any) -> str:
        if not data:
            return render_to_string(Text("No sprints found", style="yellow"))

        sprints = data if isinstance(data, list) else data.get("values", [])

        table = Table(title=f"Sprints ({len(sprints)})", box=box.ROUNDED)
        table.add_column("State", style="bold")
        table.add_column("Name")
        table.add_column("Goal", max_width=40)

        for s in sprints:
            state = s.get("state", "?")
            state_style = "green" if state == "active" else "dim"
            table.add_row(
                Text(state, style=state_style),
                s.get("name", "?"),
                (s.get("goal") or "")[:40]
            )

        return render_to_string(table)


class JiraSprintsMarkdownFormatter(MarkdownFormatter):
    """Markdown sprint formatting."""

    def format(self, data: Any) -> str:
        if not data:
            return "*No sprints found*"

        sprints = data if isinstance(data, list) else data.get("values", [])
        lines = [
            "| State | Name | Goal |",
            "|-------|------|------|",
        ]

        for s in sprints:
            lines.append(
                f"| {s.get('state', '?')} | {s.get('name', '?')} | "
                f"{(s.get('goal') or '')[:30]} |"
            )

        return "\n".join(lines)
```

### Step 2: Register Formatters

```python
# formatters/__init__.py

# Add imports
from .sprints import (
    JiraSprintsAIFormatter,
    JiraSprintsRichFormatter,
    JiraSprintsMarkdownFormatter,
)

# Add to __all__
__all__ = [
    # ...existing...
    "JiraSprintsAIFormatter",
    "JiraSprintsRichFormatter",
    "JiraSprintsMarkdownFormatter",
]

# Add to register_jira_formatters()
def register_jira_formatters():
    # ...existing registrations...

    # Sprints formatters
    formatter_registry.register("jira", "sprints", "ai", JiraSprintsAIFormatter())
    formatter_registry.register("jira", "sprints", "rich", JiraSprintsRichFormatter())
    formatter_registry.register("jira", "sprints", "markdown", JiraSprintsMarkdownFormatter())
```

### Step 3: Use in Route

```python
# In your route handler:
return formatted(data, format, "sprints")
#                              ^^^^^^^ Must match registry key
```

## Adding a Complete New Entity

Full workflow for adding support for Jira Sprints:

### 1. Create Route File

```python
# routes/sprints.py
@router.get("/sprints/{board_id}")
async def get_sprints(...): ...

@router.get("/sprint/{sprint_id}")
async def get_sprint(...): ...

@router.post("/sprint/{sprint_id}/start")
async def start_sprint(...): ...

@router.post("/sprint/{sprint_id}/close")
async def close_sprint(...): ...
```

### 2. Create Formatter File

```python
# formatters/sprints.py
class JiraSprintsAIFormatter(AIFormatter): ...
class JiraSprintsRichFormatter(RichFormatter): ...
class JiraSprintAIFormatter(AIFormatter): ...     # Single sprint
class JiraSprintRichFormatter(RichFormatter): ...
```

### 3. Update Exports

```python
# routes/__init__.py
from .sprints import router as sprints_router
# Add to create_router()

# formatters/__init__.py
from .sprints import JiraSprintsAIFormatter, ...
# Add to __all__ and register_jira_formatters()
```

### 4. Add Tests

```python
# tests/routes/test_sprints.py
import pytest
from helpers import run_cli, run_cli_raw, get_data

class TestSprintsRoutes:
    def test_get_sprints(self):
        result = run_cli("jira", "sprints", "123")
        # Assert result

    def test_get_sprints_not_found(self):
        stdout, stderr, code = run_cli_raw("jira", "sprints", "99999")
        assert "not found" in stdout.lower() or code != 0
```

### 5. Update Documentation

```markdown
# skills/jira/references/commands.md

## Sprints (Agile)

jira sprints BOARD_ID                  # List sprints
jira sprint SPRINT_ID                  # Sprint details
jira sprint SPRINT_ID --start          # Start sprint (POST)
jira sprint SPRINT_ID --close          # Close sprint (POST)
```

## Testing Your Changes

### Run Tests

```bash
cd /path/to/jira-plugin

# All tests
pytest tests/ -v

# Specific file
pytest tests/routes/test_sprints.py -v

# With coverage
pytest tests/ --cov=jira --cov-report=term-missing
```

### Manual Testing

```bash
# Restart server to pick up changes
jira restart

# Test commands
jira sprints 123
jira sprints 123 --format rich
jira sprints 123 --format json

# Check OpenAPI docs
curl -s "http://127.0.0.1:9200/openapi.json" | jq '.paths | keys'
```

### Debug Mode

```bash
# View server logs
jira logs

# Direct API call
curl -s "http://127.0.0.1:9200/jira/sprints/123?format=ai"

# Check health
jira health
```

## Common Gotchas

### 1. Formatter Not Found

**Symptom:** Returns JSON instead of formatted output

**Cause:** Formatter not registered or wrong data_type key

**Fix:**
```python
# Ensure registry key matches
formatter_registry.register("jira", "sprints", "ai", ...)
#                                    ^^^^^^^ Must match formatted(..., "sprints")
```

### 2. Path Parameter Issues

**Symptom:** 404 or parameter validation error

**Cause:** Route path doesn't match CLI translation

**Fix:** Check `bin/jira` route_request() function to understand how CLI args become HTTP paths.

### 3. Server Not Picking Up Changes

**Symptom:** Old behavior after code changes

**Fix:**
```bash
jira restart
```

### 4. Import Errors

**Symptom:** ImportError when server starts

**Fix:** Check circular imports in formatters/__init__.py and routes/__init__.py

## Jira API Reference

The `client` parameter is an `atlassian.Jira` instance. Documentation:
- https://atlassian-python-api.readthedocs.io/jira.html

Common methods:
```python
# Issues
client.issue(key)
client.create_issue(fields={...})
client.update_issue(key, fields={...})

# Search
client.jql(query, limit=50)

# Comments
client.issue_get_comments(key)
client.issue_add_comment(key, body)

# Transitions
client.get_issue_transitions(key)
client.set_issue_status_by_transition_id(key, transition_id)

# Agile
client.get_all_sprints_from_board(board_id)
client.get_sprint(sprint_id)

# Projects
client.projects()
client.project(key)
```

## Checklist for New Features

- [ ] Route handler with proper path, query params, and error handling
- [ ] Registered in `routes/__init__.py`
- [ ] Formatter classes (AI, Rich, optionally Markdown)
- [ ] Registered in `formatters/__init__.py`
- [ ] Route tests in `tests/routes/`
- [ ] Documentation in `skills/jira/references/commands.md`
- [ ] Manual testing with all formats
- [ ] Server restart and verification
