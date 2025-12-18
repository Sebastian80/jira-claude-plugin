# Tools

Pydantic-based Tool classes that define CLI commands and their behavior.

## How It Works

```
CLI: jira issue PROJ-123 --include-links
         │
         ▼
    Bridge parses args
    → GET /jira/issue/PROJ-123?include_links=true
         │
         ▼
    ToolRegistry matches route
    → GetIssue tool class
         │
         ▼
    Pydantic validates input
    → GetIssue(key="PROJ-123", include_links=True, format="ai")
         │
         ▼
    Tool.execute(ctx) runs
    → ctx.client.issue("PROJ-123")
         │
         ▼
    Returns formatted output
    → formatted(data, "ai", "issue")
```

## Available Tools

### Issues (issues.py)

| Tool | CLI | Description |
|------|-----|-------------|
| `GetIssue` | `jira issue KEY` | Get single issue with optional field validation, linked issues |
| `GetIssues` | `jira issues KEY1,KEY2` | Bulk fetch with parallel execution |
| `CreateIssue` | `jira create ...` | Create new issue |
| `UpdateIssue` | `jira update KEY ...` | Update issue fields |

### Search (search.py)

| Tool | CLI | Description |
|------|-----|-------------|
| `SearchIssues` | `jira search --jql "..."` | JQL search with pagination |

### Workflow (workflow.py)

| Tool | CLI | Description |
|------|-----|-------------|
| `GetTransitions` | `jira transitions KEY` | List available transitions |
| `Transition` | `jira transition KEY --transition "..."` | Execute transition |
| `GetWorkflows` | `jira workflows` | List workflows |

### Comments (comments.py)

| Tool | CLI | Description |
|------|-----|-------------|
| `GetComments` | `jira comments KEY` | List issue comments |
| `AddComment` | `jira comment KEY --body "..."` | Add comment |

### Worklogs (worklogs.py)

| Tool | CLI | Description |
|------|-----|-------------|
| `GetWorklogs` | `jira worklogs KEY` | List time entries |
| `AddWorklog` | `jira worklog KEY --timeSpent 2h` | Log work time |

### Links (links.py)

| Tool | CLI | Description |
|------|-----|-------------|
| `GetLinks` | `jira links KEY` | Issue-to-issue links |
| `GetLinkTypes` | `jira linktypes` | Available link types |
| `GetWebLinks` | `jira weblinks KEY` | External web links |
| `CreateIssueLink` | `jira link --inward K1 --outward K2 --type Blocks` | Create link |
| `CreateWebLink` | `jira weblink KEY --url "..." --title "..."` | Add web link |

### Others

| Module | Tools |
|--------|-------|
| `attachments.py` | `GetAttachments`, `AddAttachment` |
| `watchers.py` | `GetWatchers`, `AddWatcher`, `RemoveWatcher` |
| `projects.py` | `GetProjects`, `GetProject` |
| `components.py` | `GetComponents`, `GetComponent`, `CreateComponent`, `DeleteComponent` |
| `versions.py` | `GetVersions`, `GetVersion`, `CreateVersion`, `UpdateVersion` |
| `metadata.py` | `GetPriorities`, `GetStatuses`, `GetStatus`, `GetFields`, `GetFilters`, `GetFilter` |
| `user.py` | `GetCurrentUser`, `GetCurrentUserAlias`, `GetHealth` |

## Tool Anatomy

```python
from pydantic import Field
from toolbus.tools import Tool, ToolContext, ToolResult
from ..response import formatted

class GetIssue(Tool):
    """Get issue details by key.

    Features:
    - Field validation: warns about potentially invalid field names
    - Link expansion: --include-links fetches linked issue summaries
    """

    # Required field - no default, becomes required CLI param
    key: str = Field(..., description="Issue key like PROJ-123")

    # Optional fields - have defaults
    fields: str | None = Field(None, description="Comma-separated fields")
    expand: str | None = Field(None, description="Fields to expand (e.g., 'changelog')")
    include_links: bool = Field(False, description="Include linked issue summaries")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"           # HTTP method
        path = "/issue/{key}"    # Route path ({key} = path param)
        tags = ["issues"]        # OpenAPI grouping

    async def execute(self, ctx: ToolContext) -> Any:
        """Execute the tool. ctx.client is the Jira API client."""
        try:
            issue = ctx.client.issue(self.key, fields=self.fields)

            # Validate fields if specific fields were requested
            warning = _validate_fields(self.fields, issue)
            if warning:
                issue["_warning"] = warning

            return formatted(issue, self.format, "issue")
        except Exception as e:
            if "does not exist" in str(e).lower():
                return ToolResult(error=f"Issue {self.key} not found", status=404)
            return ToolResult(error=str(e), status=500)
```

## v1.2.0 Features

### Bulk Fetch (GetIssues)

Parallel fetching of multiple issues:

```python
class GetIssues(Tool):
    """Get multiple issues by keys in a single request."""

    keys: str = Field(..., description="Comma or space-separated issue keys")
    format: str = Field("ai", description="Output format")

    class Meta:
        method = "GET"
        path = "/issues"

    async def execute(self, ctx: ToolContext) -> Any:
        import asyncio

        keys_list = [k.strip() for k in self.keys.replace(",", " ").split()]

        def fetch_one(key: str) -> tuple[str, dict | None, str | None]:
            try:
                return (key, ctx.client.issue(key), None)
            except Exception as e:
                return (key, None, str(e))

        # Parallel fetch using thread pool (client is sync)
        tasks = [asyncio.to_thread(fetch_one, key) for key in keys_list]
        results = await asyncio.gather(*tasks)

        # Separate successes from failures
        issues = [r[1] for r in results if r[1]]
        missing = [r[0] for r in results if not r[1]]

        response = {"total": len(issues), "issues": issues}
        if missing:
            response["missing"] = missing
            response["_warning"] = f"Issues not found: {', '.join(missing)}"

        return formatted(response, self.format, "search")
```

**Usage:**
```bash
jira issues HMKG-1,HMKG-2,HMKG-3     # Comma-separated
jira issues "HMKG-1 HMKG-2 HMKG-3"  # Space-separated
```

### Field Validation

Validates requested fields against known Jira fields:

```python
KNOWN_FIELDS = {
    "summary", "description", "status", "priority", "assignee", "reporter",
    "created", "updated", "duedate", "resolution", "issuetype", "project",
    "labels", "components", "fixVersions", "issuelinks", "subtasks", "parent",
    "comment", "worklog", "attachment", "timetracking", ...
}

def _validate_fields(requested: str, issue_data: dict) -> str | None:
    """Check if requested fields returned valid data."""
    fields_list = [f.strip().lower() for f in requested.split(",")]

    # Warn about unknown fields (except customfield_*)
    unknown = [f for f in fields_list
               if f not in KNOWN_FIELDS and not f.startswith("customfield_")]

    # Warn if all fields came back as None
    fields_obj = issue_data.get("fields", {})
    none_fields = [f for f in fields_list if fields_obj.get(f) is None]

    if unknown:
        return f"Unknown fields (may be custom): {', '.join(unknown)}"
    if len(none_fields) == len(fields_list):
        return "All requested fields returned None - check field names"
    return None
```

### Linked Issues Expansion

Include linked issue summaries without additional API calls:

```python
include_links: bool = Field(False, description="Include linked issue summaries")

# In execute():
if self.include_links:
    linked_issues = _extract_linked_issues(issue)
    if linked_issues:
        issue["_linked_issues"] = linked_issues
```

The `issuelinks` field already contains linked issue data, so no extra requests needed.

**Usage:**
```bash
jira issue PROJ-123 --include-links
```

## Field Types

```python
# Required field (no default)
key: str = Field(..., description="Issue key")

# Optional field (has default)
format: str = Field("ai", description="Output format")

# Optional nullable field
fields: str | None = Field(None, description="Optional fields")

# Boolean field
include_links: bool = Field(False, description="Include links")

# Field with alias (CLI uses alias)
time_spent: str = Field(..., alias="timeSpent", description="Time spent")
# CLI: --timeSpent 2h
# Code: self.time_spent
```

## ToolContext

Passed to `execute()`, provides access to:

```python
async def execute(self, ctx: ToolContext) -> Any:
    ctx.client      # Jira API client (atlassian-python-api)
    ctx.connector   # JiraConnector instance
    ctx.request     # FastAPI request (rarely needed)
    ctx.format      # Formatter function (rarely needed directly)
```

## Return Types

### ToolResult (Structured)

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

# Auto-selects formatter based on entity type
return formatted(issue_data, self.format, "issue")
return formatted(comments, self.format, "comments")
return formatted(search_results, self.format, "search")
```

## Common Patterns

### GET with Formatting

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

### POST with Validation

```python
class DoAction(Tool):
    key: str = Field(..., description="Target key")
    action: str = Field(..., description="Action to perform")

    class Meta:
        method = "POST"
        path = "/action/{key}"

    async def execute(self, ctx: ToolContext) -> Any:
        # Get available actions
        available = ctx.client.get_available_actions(self.key)
        action_names = [a["name"] for a in available]

        # Find matching action
        match = next((a for a in available
                     if a["name"].lower() == self.action.lower()), None)

        if not match:
            return ToolResult(
                error=f"Action '{self.action}' not available. Options: {action_names}",
                status=400
            )

        ctx.client.perform_action(self.key, match["id"])
        return ToolResult(data={"key": self.key, "action": self.action})
```

### Error Handling

```python
async def execute(self, ctx: ToolContext) -> Any:
    try:
        result = ctx.client.some_method(self.key)
        return formatted(result, self.format, "entity")
    except Exception as e:
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "404" in error_msg:
            return ToolResult(error=f"Entity {self.key} not found", status=404)
        if "permission" in error_msg or "403" in error_msg:
            return ToolResult(error="Permission denied", status=403)
        if "401" in error_msg:
            return ToolResult(error="Authentication failed", status=401)
        return ToolResult(error=str(e), status=500)
```

## CLI Mapping

```
Tool Class          CLI Command
────────────────────────────────────────────────────
GetIssue         →  jira issue KEY
GetIssues        →  jira issues KEY1,KEY2
CreateIssue      →  jira create --project X --summary Y
SearchIssues     →  jira search --jql "..."
GetTransitions   →  jira transitions KEY
Transition       →  jira transition KEY --transition "..."
AddComment       →  jira comment KEY --body "text"
AddWorklog       →  jira worklog KEY --timeSpent 2h
```

- Path params (`{key}`) become positional args
- Fields become `--param` flags
- Aliases (`alias="timeSpent"`) preserve Jira naming

## Jira Client Methods

The `ctx.client` is an `atlassian.Jira` instance:

```python
# Issues
ctx.client.issue(key)
ctx.client.issue(key, fields="summary,status")
ctx.client.issue(key, expand="changelog")
ctx.client.create_issue(fields={...})
ctx.client.update_issue_field(key, fields={...})

# Search
ctx.client.jql(query, limit=50, start=0)

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

# User
ctx.client.myself()
```

Full API: https://atlassian-python-api.readthedocs.io/jira.html

## Adding a New Tool

### 1. Create Tool Class

```python
# tools/myfeature.py

class GetSprints(Tool):
    """Get active sprints for a board."""

    board_id: str = Field(..., description="Board ID")
    state: str = Field("active", description="Sprint state")
    format: str = Field("ai", description="Output format")

    class Meta:
        method = "GET"
        path = "/sprints/{board_id}"
        tags = ["agile"]

    async def execute(self, ctx: ToolContext) -> Any:
        sprints = ctx.client.get_all_sprints_from_board(
            self.board_id, state=self.state
        )
        return formatted(sprints, self.format, "sprints")
```

### 2. Export in __init__.py

```python
# tools/__init__.py

from .myfeature import GetSprints

ALL_TOOLS = [
    # ...existing...
    GetSprints,
]
```

### 3. Done

No additional wiring needed. Routes, CLI help, and OpenAPI docs are auto-generated.
