# Tools

Pydantic-based Tool classes that define CLI commands and their behavior.

## How It Works

```
CLI: jira comment PROJ-123 --body "Done"
         │
         ▼
    Bridge parses args
         │
         ▼
    Matches Tool class: AddComment
         │
         ▼
    Pydantic validates input
         │
         ▼
    Tool.execute(ctx) runs
         │
         ▼
    Returns ToolResult or formatted data
```

## Tool Anatomy

```python
from pydantic import Field
from toolbus.tools import Tool, ToolContext, ToolResult

class AddComment(Tool):
    """Add comment to an issue."""  # ← Shows in CLI help

    # Fields become CLI params
    key: str = Field(..., description="Issue key")           # --key (required)
    body: str = Field(..., description="Comment text")       # --body (required)
    format: str = Field("ai", description="Output format")   # --format (optional, default: ai)

    class Meta:
        method = "POST"           # HTTP method (for OpenAPI)
        path = "/comment/{key}"   # Route path, {key} from field
        tags = ["comments"]       # OpenAPI grouping

    async def execute(self, ctx: ToolContext) -> Any:
        """Run the tool. ctx.client is the Jira API client."""
        result = ctx.client.issue_add_comment(self.key, self.body)
        return ToolResult(data=result, status=201)
```

## Field Types

```python
# Required field (no default)
key: str = Field(..., description="Issue key")

# Optional field (has default)
format: str = Field("ai", description="Output format")

# Optional nullable field
comment: str | None = Field(None, description="Optional comment")

# Field with alias (CLI uses alias, code uses field name)
time_spent: str = Field(..., alias="timeSpent", description="Time spent")
# CLI: --timeSpent 2h
# Code: self.time_spent
```

## ToolContext

Passed to `execute()`, provides:

```python
async def execute(self, ctx: ToolContext) -> Any:
    ctx.client      # Jira API client (atlassian-python-api)
    ctx.connector   # JiraConnector instance
    ctx.params      # Raw request params (rarely needed)
```

## Return Types

### ToolResult

```python
# Success
return ToolResult(data={"key": "PROJ-123"})
return ToolResult(data=result, status=201)  # Created

# Error
return ToolResult(error="Issue not found", status=404)
return ToolResult(error=str(e), status=500)
```

### Formatted Output

```python
from ..response import formatted

# Auto-selects formatter based on entity type and format param
return formatted(issue_data, self.format, "issue")
return formatted(comments, self.format, "comments")
```

## Adding a New Tool

### 1. Choose or create file

```
tools/
├── issues.py      # Issue CRUD
├── search.py      # JQL search
├── workflow.py    # Transitions, workflows
├── comments.py    # Comments
├── worklogs.py    # Time tracking
├── links.py       # Issue links, web links
├── attachments.py # Attachments
├── watchers.py    # Watchers
├── projects.py    # Projects
├── components.py  # Components
├── versions.py    # Versions
├── metadata.py    # Fields, statuses, priorities, filters
├── user.py        # User info, health check
```

### 2. Create Tool class

```python
# tools/comments.py

class DeleteComment(Tool):
    """Delete a comment from an issue."""

    key: str = Field(..., description="Issue key")
    comment_id: str = Field(..., alias="commentId", description="Comment ID")

    class Meta:
        method = "DELETE"
        path = "/comment/{key}/{comment_id}"
        tags = ["comments"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            ctx.client.issue_delete_comment(self.key, self.comment_id)
            return ToolResult(data={"deleted": self.comment_id})
        except Exception as e:
            return ToolResult(error=str(e), status=400)
```

### 3. Export in __init__.py

```python
# tools/__init__.py

from .comments import GetComments, AddComment, DeleteComment  # Add new one

__all__ = [
    # ...existing...
    "DeleteComment",
]
```

### 4. Done

- CLI help auto-generated from Field descriptions
- Route auto-registered from Meta.path
- No manual wiring needed

## CLI Mapping

```
Tool Class          CLI Command
──────────────────────────────────────────
GetIssue         →  jira issue KEY
CreateIssue      →  jira create --project X --summary Y
Search           →  jira search --jql "..."
GetTransitions   →  jira transitions KEY
Transition       →  jira transition KEY --transition "In Progress"
AddComment       →  jira comment KEY --body "text"
AddWorklog       →  jira worklog KEY --timeSpent 2h
```

Path params (`{key}`) become positional args.
Fields become `--param` flags.

## Common Patterns

### GET with formatting

```python
class GetComments(Tool):
    key: str = Field(..., description="Issue key")
    format: str = Field("ai", description="Output format")

    class Meta:
        method = "GET"
        path = "/comments/{key}"

    async def execute(self, ctx: ToolContext) -> Any:
        result = ctx.client.issue_get_comments(self.key)
        comments = result.get("comments", [])
        return formatted(comments, self.format, "comments")
```

### POST with validation

```python
class Transition(Tool):
    key: str = Field(..., description="Issue key")
    transition: str = Field(..., description="Transition name or ID")

    class Meta:
        method = "POST"
        path = "/transition/{key}"

    async def execute(self, ctx: ToolContext) -> Any:
        # Get available transitions
        transitions = ctx.client.get_issue_transitions(self.key)

        # Find matching transition
        transition_id = None
        for t in transitions:
            if t["name"].lower() == self.transition.lower():
                transition_id = t["id"]
                break

        if not transition_id:
            available = [t["name"] for t in transitions]
            return ToolResult(
                error=f"Transition '{self.transition}' not found. Available: {available}",
                status=400
            )

        ctx.client.set_issue_status_by_transition_id(self.key, transition_id)
        return ToolResult(data={"key": self.key, "transition": self.transition})
```

### Error handling

```python
async def execute(self, ctx: ToolContext) -> Any:
    try:
        result = ctx.client.some_method(self.key)
        return formatted(result, self.format, "entity")
    except Exception as e:
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "404" in error_msg:
            return ToolResult(error=f"Issue {self.key} not found", status=404)
        if "permission" in error_msg or "403" in error_msg:
            return ToolResult(error="Permission denied", status=403)
        return ToolResult(error=str(e), status=500)
```

## Jira Client Methods

The `ctx.client` is an `atlassian.Jira` instance. Common methods:

```python
# Issues
ctx.client.issue(key)
ctx.client.issue(key, fields="summary,status")
ctx.client.create_issue(fields={...})
ctx.client.update_issue(key, fields={...})

# Search
ctx.client.jql(jql_query, limit=50)

# Comments
ctx.client.issue_get_comments(key)
ctx.client.issue_add_comment(key, body)

# Worklogs
ctx.client.issue_get_worklog(key)
ctx.client.issue_add_json_worklog(key, {"timeSpent": "2h"})

# Transitions
ctx.client.get_issue_transitions(key)
ctx.client.set_issue_status_by_transition_id(key, transition_id)

# Links
ctx.client.create_issue_link(data)
ctx.client.create_or_update_issue_remote_links(key, url, title)

# Watchers
ctx.client.issue_get_watchers(key)
ctx.client.issue_add_watcher(key, username)
ctx.client.issue_delete_watcher(key, username)

# Projects
ctx.client.projects()
ctx.client.project(key)
ctx.client.get_project_components(project)
ctx.client.get_project_versions(project)
```

Full API: https://atlassian-python-api.readthedocs.io/jira.html
