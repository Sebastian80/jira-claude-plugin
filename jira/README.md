# Jira Package Internals

Internal architecture and component documentation for the `jira/` Python package.

## Package Structure

```
jira/
├── __init__.py      # Package init, formatter registration
├── main.py          # FastAPI server entry point
├── deps.py          # Dependency injection (fresh client per request)
├── response.py      # Response formatting utilities
│
├── routes/          # FastAPI route handlers
│   ├── __init__.py  # create_router() - combines all routes
│   ├── issues.py    # GET /issue/{key}, POST /create, PATCH /issue/{key}
│   ├── search.py    # GET /search (JQL)
│   ├── workflow.py  # GET /transitions, POST /transition
│   ├── comments.py  # GET /comments, POST /comment
│   ├── worklogs.py  # GET /worklogs, POST /worklog
│   ├── links.py     # Issue links and web links
│   ├── attachments.py
│   ├── watchers.py
│   ├── projects.py
│   ├── components.py
│   ├── versions.py
│   ├── statuses.py
│   ├── priorities.py
│   ├── fields.py
│   ├── filters.py
│   ├── user.py
│   ├── health.py
│   └── help.py      # Self-documenting /help endpoint
│
├── formatters/      # Output formatters (AI, Rich, Markdown)
│   ├── __init__.py  # Registry, registration function
│   ├── base.py      # Base classes, utilities
│   ├── issue.py     # Issue formatters
│   ├── search.py    # Search results formatters
│   └── ...          # Entity-specific formatters
│
└── lib/             # Shared utilities
    ├── client.py    # get_jira_client() factory
    ├── config.py    # Environment config loading
    ├── output.py    # Output helpers
    └── workflow.py  # Workflow utilities
```

## Request Flow

```
1. CLI Input
   jira issue PROJ-123 --format ai
          │
          ▼
2. bin/jira (Bash wrapper)
   Ensures server running, converts args to HTTP
   GET http://127.0.0.1:9200/jira/issue/PROJ-123?format=ai
          │
          ▼
3. FastAPI Server (main.py)
   Routes to /jira/* handlers
          │
          ▼
4. Route Handler (routes/issues.py)
   get_issue(key, format, client=Depends(jira))
          │
          ▼
5. Dependency Injection (deps.py)
   jira() → fresh client per request
          │
          ▼
6. Jira API
   client.issue("PROJ-123")
   HTTPS request to Jira Cloud/Server
          │
          ▼
7. Response Formatting (response.py)
   formatted(data, "ai", "issue")
   → FormatterRegistry.get("ai", "jira", "issue")
   → JiraIssueAIFormatter.format(data)
          │
          ▼
8. CLI Output
   PlainTextResponse → stdout
```

## Key Components

### main.py - Server Entry Point

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Jira client singleton
    init_client()
    yield
    # Shutdown: Cleanup
    reset()

app = FastAPI(lifespan=lifespan)
app.include_router(create_router(), prefix="/jira")
```

### deps.py - Dependency Injection

```python
def jira():
    """FastAPI dependency - get fresh Jira client per request."""
    try:
        return get_jira_client()
    except Exception as e:
        raise HTTPException(503, f"Jira not connected: {e}")
```

Fresh client per request avoids stale TCP connection issues after long idle periods.
The ~100ms overhead is negligible for CLI usage.

### response.py - Output Formatting

```python
def formatted(data: Any, fmt: str, data_type: str | None = None):
    """Format API response for output."""
    if fmt == "json":
        return JSONResponse({"success": True, "data": data})

    # Look up plugin-specific formatter
    formatter = formatter_registry.get(fmt, plugin="jira", data_type=data_type)
    if formatter:
        return PlainTextResponse(formatter.format(data))

    # Fallback to JSON
    return JSONResponse({"success": True, "data": data})
```

### routes/__init__.py - Router Assembly

```python
def create_router() -> APIRouter:
    router = APIRouter()

    router.include_router(health_router)
    router.include_router(help_router)
    router.include_router(issues_router)
    router.include_router(search_router)
    # ... all other route modules

    return router
```

## Route Pattern

Each route module follows this pattern:

```python
# routes/issues.py
from fastapi import APIRouter, Depends, Query
from ..deps import jira
from ..response import formatted, formatted_error

router = APIRouter()

@router.get("/issue/{key}")
async def get_issue(
    key: str,
    format: str = Query("json", description="Output format"),
    client=Depends(jira),
):
    """Get issue details by key."""
    try:
        issue = client.issue(key)
        return formatted(issue, format, "issue")
    except Exception as e:
        if "not found" in str(e).lower():
            return formatted_error(f"Issue {key} not found", fmt=format, status=404)
        raise HTTPException(status_code=500, detail=str(e))
```

## Formatter Registration

Formatters are registered by (plugin, data_type, format):

```python
# In formatters/__init__.py

def register_jira_formatters():
    # Issue formatters
    formatter_registry.register("jira", "issue", "ai", JiraIssueAIFormatter())
    formatter_registry.register("jira", "issue", "rich", JiraIssueRichFormatter())
    formatter_registry.register("jira", "issue", "markdown", JiraIssueMarkdownFormatter())

    # Search formatters
    formatter_registry.register("jira", "search", "ai", JiraSearchAIFormatter())
    # ...
```

Lookup:
```python
formatter_registry.get("ai", plugin="jira", data_type="issue")
# Returns JiraIssueAIFormatter instance
```

## Configuration

Loaded from `~/.env.jira` by `lib/config.py`:

```bash
# Cloud
JIRA_URL=https://company.atlassian.net
JIRA_USERNAME=email@example.com
JIRA_API_TOKEN=token

# Server/DC
JIRA_URL=https://jira.company.com
JIRA_PERSONAL_TOKEN=pat
```

Auto-detection:
- `JIRA_PERSONAL_TOKEN` present → Server/DC PAT auth
- `JIRA_USERNAME` + `JIRA_API_TOKEN` → Cloud basic auth
- URL contains `.atlassian.net` → Cloud mode

## Debugging

```bash
# Server health
jira health

# Server logs
jira logs

# Direct API call
curl "http://127.0.0.1:9200/jira/issue/PROJ-123"

# OpenAPI spec
curl "http://127.0.0.1:9200/openapi.json" | jq '.paths | keys'

# Restart after code changes
jira restart
```

## See Also

- [../ARCHITECTURE.md](../ARCHITECTURE.md) - System-wide architecture
- [../EXTENDING.md](../EXTENDING.md) - Adding new functionality
- [formatters/README.md](formatters/README.md) - Formatter system
