# Extending the Jira Plugin

Step-by-step guide to adding new functionality to the Jira plugin.

## Quick Reference

| Extension Type | Files to Modify | Complexity |
|----------------|-----------------|------------|
| New Tool (command) | `tools/<category>.py`, `tools/__init__.py` | Low |
| New Formatter | `formatters/<entity>.py`, `formatters/__init__.py` | Low |
| New Entity (full) | Tools + Formatters + Tests + Docs | Medium |
| New Connector feature | `connector.py` | Medium |
| New CLI behavior | `plugin_router.py` (bridge) | High |

## Adding a New Tool

Tools are CLI commands. Each Tool class = one CLI command.

### Step 1: Create the Tool Class

```python
# tools/myfeature.py (or add to existing file like tools/issues.py)

from pydantic import Field
from toolbus.tools import Tool, ToolContext, ToolResult
from ..response import formatted

class GetSprints(Tool):
    """Get active sprints for a board.

    Lists all active sprints including their goals and dates.
    Useful for planning and status checks.
    """

    # Required field (no default) - becomes required CLI param
    board_id: str = Field(..., description="Agile board ID")

    # Optional fields - have defaults
    state: str = Field("active", description="Sprint state: active, closed, future")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/sprints/{board_id}"
        tags = ["agile"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            # ctx.client is the atlassian.Jira instance
            sprints = ctx.client.get_all_sprints_from_board(
                self.board_id,
                state=self.state
            )
            return formatted(sprints, self.format, "sprints")
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                return ToolResult(error=f"Board {self.board_id} not found", status=404)
            return ToolResult(error=str(e), status=500)
```

### Step 2: Export in __init__.py

```python
# tools/__init__.py

from .myfeature import GetSprints  # Add import

ALL_TOOLS = [
    # ...existing tools...
    GetSprints,  # Add to list
]

__all__ = [
    # ...existing exports...
    "GetSprints",
]
```

### Step 3: Done!

The tool is now available:
```bash
jira sprints 123                    # GET /jira/sprints/123
jira sprints 123 --state closed     # GET /jira/sprints/123?state=closed
jira help sprints                   # Auto-generated help
```

## Tool Patterns

### Pattern: GET with Formatting

```python
class GetEntity(Tool):
    key: str = Field(..., description="Entity key")
    format: str = Field("ai", description="Output format")

    class Meta:
        method = "GET"
        path = "/entity/{key}"

    async def execute(self, ctx: ToolContext) -> Any:
        data = ctx.client.get_entity(self.key)
        return formatted(data, self.format, "entity")
```

### Pattern: POST with Validation

```python
class CreateEntity(Tool):
    name: str = Field(..., description="Entity name")
    project: str = Field(..., description="Project key")

    class Meta:
        method = "POST"
        path = "/entity"

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            result = ctx.client.create_entity(
                name=self.name,
                project=self.project
            )
            return ToolResult(data=result, status=201)
        except Exception as e:
            return ToolResult(error=str(e), status=400)
```

### Pattern: Bulk Fetch (Parallel)

```python
class GetEntities(Tool):
    keys: str = Field(..., description="Comma-separated keys")
    format: str = Field("ai", description="Output format")

    class Meta:
        method = "GET"
        path = "/entities"

    async def execute(self, ctx: ToolContext) -> Any:
        import asyncio

        keys_list = [k.strip() for k in self.keys.split(",")]

        def fetch_one(key: str) -> tuple[str, dict | None, str | None]:
            try:
                return (key, ctx.client.get_entity(key), None)
            except Exception as e:
                return (key, None, str(e))

        tasks = [asyncio.to_thread(fetch_one, k) for k in keys_list]
        results = await asyncio.gather(*tasks)

        entities = [r[1] for r in results if r[1]]
        errors = [f"{r[0]}: {r[2]}" for r in results if r[2]]

        return formatted({"entities": entities, "errors": errors}, self.format, "entities")
```

### Pattern: Operation with Available Options

```python
class DoSomething(Tool):
    key: str = Field(..., description="Target key")
    action: str = Field(..., description="Action to perform")

    class Meta:
        method = "POST"
        path = "/do/{key}"

    async def execute(self, ctx: ToolContext) -> Any:
        # Get available actions
        available = ctx.client.get_available_actions(self.key)
        action_names = [a["name"] for a in available]

        # Find matching action
        match = None
        for a in available:
            if a["name"].lower() == self.action.lower():
                match = a
                break

        if not match:
            return ToolResult(
                error=f"Action '{self.action}' not available. Options: {action_names}",
                status=400
            )

        # Perform action
        ctx.client.perform_action(self.key, match["id"])
        return ToolResult(data={"key": self.key, "action": self.action})
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

### Step 3: Use in Tool

```python
# In your tool's execute():
return formatted(data, self.format, "sprints")
#                                    └─ Matches registry key
```

## Adding a Complete New Entity

Full workflow for adding support for Jira Sprints:

### 1. Create Tool File

```python
# tools/sprints.py
class GetSprints(Tool): ...
class GetSprint(Tool): ...
class CreateSprint(Tool): ...
class StartSprint(Tool): ...
class CloseSprint(Tool): ...
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
# tools/__init__.py
from .sprints import GetSprints, GetSprint, CreateSprint, StartSprint, CloseSprint
ALL_TOOLS = [..., GetSprints, GetSprint, CreateSprint, StartSprint, CloseSprint]

# formatters/__init__.py
from .sprints import JiraSprintsAIFormatter, ...
def register_jira_formatters():
    formatter_registry.register("jira", "sprints", "ai", JiraSprintsAIFormatter())
    formatter_registry.register("jira", "sprint", "ai", JiraSprintAIFormatter())
    # ...
```

### 4. Add Tests

```python
# tests/routes/test_sprints.py
import pytest
from tests.routes.helpers import call_bridge

class TestSprintsRoutes:
    def test_get_sprints(self):
        result = call_bridge(["jira", "sprints", "123"])
        assert result.returncode == 0

    def test_get_sprints_not_found(self):
        result = call_bridge(["jira", "sprints", "99999"])
        assert "not found" in result.stdout.lower() or result.returncode != 0
```

### 5. Update Documentation

```markdown
# skills/jira/references/commands.md

## Sprints (Agile)

jira sprints BOARD_ID                  # List sprints
jira sprint SPRINT_ID                  # Sprint details
jira sprint SPRINT_ID --start          # Start sprint
jira sprint SPRINT_ID --close          # Close sprint
```

## Testing Your Changes

### Run Tests

```bash
cd ~/.claude/plugins/marketplaces/sebastian-marketplace/plugins/jira

# All tests
uv run pytest tests/ -v

# Specific file
uv run pytest tests/routes/test_sprints.py -v

# With coverage
uv run pytest tests/ --cov=jira --cov-report=term-missing
```

### Manual Testing

```bash
# Reload plugin
~/.claude/.../ai-tool-bridge/.venv/bin/bridge reload

# Test commands
jira sprints 123
jira sprints 123 --format rich
jira sprints 123 --format json

# Check help
jira help sprints
```

### Debug Mode

```bash
# View daemon logs
tail -f ~/.local/share/ai-tool-bridge/logs/daemon.log

# Direct API call
curl -s "http://[::1]:9100/jira/sprints/123?format=ai"

# Check OpenAPI
curl -s "http://[::1]:9100/openapi.json" | jq '.paths["/jira/sprints/{board_id}"]'
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

**Cause:** Field name doesn't match path placeholder

**Fix:**
```python
class Meta:
    path = "/entity/{key}"  # Placeholder name
                    ^^^
key: str = Field(...)       # Field name must match
^^^
```

### 3. Optional Field with None Default

**Symptom:** Field treated as required

**Fix:**
```python
# Correct way to define optional field
field: str | None = Field(None, description="...")
#           ^^^^           ^^^^
#           Allow None     Default to None
```

### 4. Circuit Breaker Blocking Requests

**Symptom:** 503 errors after failures

**Fix:**
```bash
# Check circuit state
jira health

# Wait 30s for half_open state, then successful request resets
# Or restart daemon to reset circuit breaker
~/.claude/.../ai-tool-bridge/.venv/bin/bridge restart
```

## Jira API Reference

The `ctx.client` is an `atlassian.Jira` instance. Documentation:
- https://atlassian-python-api.readthedocs.io/jira.html

Common methods:
```python
# Issues
ctx.client.issue(key)
ctx.client.create_issue(fields={...})
ctx.client.update_issue(key, fields={...})

# Search
ctx.client.jql(query, limit=50)

# Comments
ctx.client.issue_get_comments(key)
ctx.client.issue_add_comment(key, body)

# Transitions
ctx.client.get_issue_transitions(key)
ctx.client.set_issue_status_by_transition_id(key, transition_id)

# Agile
ctx.client.get_all_sprints_from_board(board_id)
ctx.client.get_sprint(sprint_id)

# Projects
ctx.client.projects()
ctx.client.project(key)
```

## Checklist for New Features

- [ ] Tool class with proper fields, Meta, and execute()
- [ ] Exported in `tools/__init__.py`
- [ ] Formatter classes (AI, Rich, optionally Markdown)
- [ ] Registered in `formatters/__init__.py`
- [ ] Route tests in `tests/routes/`
- [ ] Documentation in `skills/jira/references/commands.md`
- [ ] Manual testing with all formats
- [ ] Error handling for common failures (404, 401, etc.)
