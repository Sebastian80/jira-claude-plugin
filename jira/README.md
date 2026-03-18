# Jira Package Internals

Internal architecture and component documentation for the `jira/` Python package.

## Package Structure

```
jira/
├── __init__.py      # Package init, version from importlib.metadata, triggers formatter registration
├── main.py          # FastAPI server entry point
├── deps.py          # Dependency injection (cached Jira client singleton + user timezone)
├── response.py      # Response formatting utilities + error handler decorator
│
├── routes/          # FastAPI route handlers (all sync def, not async)
│   ├── __init__.py  # create_router() - combines all routes
│   ├── issues.py    # GET /issue/{key}, GET /show/{key}, POST /create, PATCH /issue/{key}, DELETE /delete/{key}
│   ├── search.py    # GET /search (JQL)
│   ├── workflow.py  # GET /transitions, POST /transition
│   ├── comments.py  # GET /comments, POST /comment, DELETE /comment/{key}/{id}
│   ├── worklogs.py  # GET /worklogs, POST /worklog
│   ├── links.py     # Issue links, web links, link types
│   ├── attachments.py
│   ├── watchers.py
│   ├── projects.py
│   ├── components.py
│   ├── versions.py
│   ├── statuses.py
│   ├── priorities.py
│   ├── fields.py
│   ├── filters.py
│   ├── agile.py     # Boards, sprints, sprint issue management
│   ├── user.py
│   ├── health.py
│   └── help.py      # Self-documenting /help endpoint from OpenAPI spec
│
├── formatters/      # Output formatters (AI, Rich, Markdown)
│   ├── __init__.py  # Auto-registration imports + base re-exports
│   ├── base.py      # Base classes, registry, utilities, icons/styles
│   ├── issue.py     # Issue formatters
│   ├── show.py      # Combined issue + comments view
│   ├── search.py    # Search results formatters
│   └── ...          # Entity-specific formatters (18 modules total)
│
└── lib/             # Shared utilities
    ├── client.py    # JiraClient (Jira subclass with attachment MIME fix)
    ├── config.py    # Environment config loading from ~/.env.jira
    └── workflow.py  # Workflow engine (BFS pathfinding, smart transitions)
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
   jira() → cached singleton client
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
    # Startup: Initialize cached Jira client + user timezone
    init_client()
    yield
    # Shutdown: nothing to clean up

app = FastAPI(lifespan=lifespan)
app.include_router(create_router(), prefix="/jira")
```

### deps.py - Dependency Injection

```python
_client: Jira | None = None
_user_tz: ZoneInfo = ZoneInfo("UTC")

def init_client():
    global _client, _user_tz
    _client = get_jira_client()
    user = _client.myself()
    _user_tz = ZoneInfo(user.get("timeZone") or "UTC")

def jira() -> Jira:
    """FastAPI dependency — return the cached Jira client."""
    if _client is None:
        raise HTTPException(status_code=503, detail="Jira client not initialized")
    return _client
```

The `atlassian-python-api` library uses `requests.Session` internally, which handles connection pooling and keep-alive.

### response.py - Output Formatting

```python
OutputFormat = Literal["json", "rich", "ai", "markdown"]
FORMAT_QUERY = Query("json", description="Output format: json, rich, ai, markdown")

def formatted(data: Any, fmt: OutputFormat, data_type: str | None = None) -> Response:
    if fmt == "json":
        return success(data)
    formatter = formatter_registry.get(fmt, plugin="jira", data_type=data_type)
    if formatter:
        return PlainTextResponse(formatter.format(data))
    return success(data)  # fallback
```

## Route Pattern

Each route module follows this pattern:

```python
from fastapi import APIRouter, Depends, Query
from ..deps import jira
from ..response import formatted, jira_error_handler, OutputFormat, FORMAT_QUERY

router = APIRouter()

@router.get("/issue/{key}")
@jira_error_handler(not_found="Issue {key} not found")
def get_issue(
    key: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    issue = client.issue(key)
    return formatted(issue, format, "issue")
```

**Note:** All route handlers are sync `def` (not `async def`) because they call the sync `atlassian-python-api` library. FastAPI runs sync handlers in a threadpool automatically.

## Formatter Registration

Formatters auto-register via the `@register_formatter` class decorator:

```python
@register_formatter("jira", "issue", "ai")
class JiraIssueAIFormatter(AIFormatter):
    def format(self, data: Any) -> str:
        ...
```

Registration happens when the module is imported. `jira/__init__.py` imports `jira.formatters` which triggers all decorator registrations.

## Configuration

Loaded from `~/.env.jira` by `lib/config.py`. Supports Cloud (username + API token) and Server/DC (personal access token) authentication.

## See Also

- [../ARCHITECTURE.md](../ARCHITECTURE.md) - System-wide architecture
- [../EXTENDING.md](../EXTENDING.md) - Adding new functionality
- [formatters/README.md](formatters/README.md) - Formatter system
