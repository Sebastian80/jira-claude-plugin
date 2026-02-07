# Jira Plugin Architecture

Deep dive into how the standalone Jira plugin works, how components connect, and the data flow from CLI to Jira API.

## System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              USER / AI AGENT                               │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ jira issue PROJ-123
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  bin/jira (Self-Bootstrapping Bash Wrapper)                                │
│  ──────────────────────────────────────────                                │
│  1. Ensures venv exists (auto-creates on first run)                        │
│  2. Ensures server is running (auto-starts if needed)                      │
│  3. Converts CLI args to HTTP request                                      │
│  4. Routes: jira issue PROJ-123 → GET /jira/issue/PROJ-123                 │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ GET http://127.0.0.1:9200/jira/issue/PROJ-123
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Standalone FastAPI Server (main.py, port 9200)                            │
│  ──────────────────────────────────────────────                            │
│  • Self-contained - no external dependencies                               │
│  • Creates fresh Jira client per request (avoids stale connections)        │
│  • Routes requests to endpoint handlers                                    │
│  • Provides OpenAPI documentation                                          │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Routes to /jira/* handlers
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Route Handlers (routes/*.py)                                              │
│  ────────────────────────────                                              │
│  • issues.py: GET /issue/{key}, POST /create, PATCH /issue/{key}           │
│  • search.py: GET /search?jql=...                                          │
│  • comments.py: GET/POST /comments/{key}                                   │
│  • workflow.py: GET /transitions/{key}, POST /transition/{key}             │
│  • ... 20 route modules total                                              │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Depends(jira) injection
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Dependency Injection (deps.py)                                            │
│  ──────────────────────────────                                            │
│  • Fresh Jira client per request (no stale connections)                    │
│  • Health check on startup                                                 │
│  • FastAPI Depends() integration                                           │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ client.issue("PROJ-123")
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  atlassian-python-api (Jira Client)                                        │
│  ──────────────────────────────────                                        │
│  • Third-party library wrapping Jira REST API                              │
│  • Handles authentication (Cloud or Server/DC)                             │
│  • Returns JSON responses                                                  │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS API call
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Jira API (Cloud or Server/DC)                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ JSON response
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  FormatterRegistry (formatters/)                                           │
│  ───────────────────────────────                                           │
│  • Looks up formatter by: plugin + data_type + format                      │
│  • Example: jira:issue:ai → JiraIssueAIFormatter                           │
│  • Returns token-efficient structured text                                 │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ PlainTextResponse / JSONResponse
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Back through the stack to CLI output                                      │
└────────────────────────────────────────────────────────────────────────────┘
```

## Component Deep Dive

### 1. CLI Wrapper (bin/jira)

Self-bootstrapping bash script that handles all setup automatically:

```bash
# First run: creates venv, installs deps, starts server
jira issue PROJ-123

# Subsequent runs: just routes to running server
jira issue PROJ-123
```

**Key features:**
- Auto-creates Python venv in `~/.local/share/jira-cli/.venv`
- Auto-installs dependencies (fastapi, uvicorn, atlassian-python-api, etc.)
- Auto-starts server on first command
- PID file management for server lifecycle

**CLI to HTTP translation:**
```
GET requests: args become query parameters
  jira issue PROJ-123 --format ai
  → GET /jira/issue/PROJ-123?format=ai

POST/PATCH requests: args become JSON body (except --format)
  jira comment PROJ-123 --text "Hello"
  → POST /jira/comment/PROJ-123 with body {"text": "Hello"}

DELETE requests: positional args become path segments
  jira comment PROJ-123 12345 -X DELETE
  → DELETE /jira/comment/PROJ-123/12345
```

### 2. FastAPI Server (main.py)

Standalone server with lifecycle management:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Jira client
    init_client()
    yield
    # Shutdown: Cleanup
    reset()

app = FastAPI(lifespan=lifespan)
app.include_router(create_router(), prefix="/jira")
```

**Endpoints:**
- `/health` - Server and Jira connection health
- `/` - Basic info
- `/jira/*` - All Jira operations

### 3. Route Modules (routes/*.py)

Each module handles a specific domain:

| Module | Endpoints | Purpose |
|--------|-----------|---------|
| issues.py | `/issue/{key}`, `/create`, `/delete/{key}` | Issue CRUD |
| search.py | `/search` | JQL queries |
| comments.py | `/comments/{key}`, `/comment/{key}`, DELETE `/comment/{key}/{id}` | Comments |
| workflow.py | `/transitions/{key}`, `/transition/{key}` | Status changes |
| watchers.py | `/watchers/{key}`, `/watcher/{key}` | Watchers |
| attachments.py | `/attachments/{key}`, `/attachment/{key}` | Files |
| links.py | `/links/{key}`, `/linktypes` | Issue links |
| worklogs.py | `/worklogs/{key}`, `/worklog/{key}` | Time tracking |
| projects.py | `/projects`, `/project/{key}` | Projects |
| statuses.py | `/statuses`, `/status/{name}` | Status metadata |
| priorities.py | `/priorities` | Priority metadata |
| components.py | `/components/{project}`, `/component/{id}` | Component CRUD |
| versions.py | `/versions/{project}`, `/version/{id}` | Version/release management |
| agile.py | `/boards`, `/sprints/{board}`, `/sprint/{id}` | Sprints and boards |
| filters.py | `/filters`, `/filter/{id}` | Saved filters |
| fields.py | `/fields`, `/fields/custom` | Field metadata |
| user.py | `/user/me` | Current user |
| health.py | `/health` | Health check |
| help.py | `/help`, `/help/{endpoint}` | API docs |

### 4. Dependency Injection (deps.py)

Fresh client per request - simple and reliable:

```python
def jira():
    """FastAPI dependency - get fresh Jira client per request."""
    try:
        return get_jira_client()
    except Exception as e:
        raise HTTPException(503, f"Jira not connected: {e}")
```

**Why fresh per request?**
- Avoids stale TCP connections after long idle periods
- No complex reconnection/circuit breaker logic needed
- ~100ms overhead is negligible for CLI usage

### 5. Formatter System (formatters/)

Transforms API responses for different consumers:

```
                          ┌─────────────────────┐
                          │  FormatterRegistry  │
                          │  ─────────────────  │
                          │  Stores formatters  │
                          │  by plugin:type:fmt │
                          └─────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │ AIFormat  │   │ RichFormat│   │ MDFormat  │
            │ ───────── │   │ ───────── │   │ ───────── │
            │ Compact   │   │ Colors    │   │ Tables    │
            │ Structured│   │ Panels    │   │ Links     │
            └───────────┘   └───────────┘   └───────────┘
```

**Registration:**
```python
formatter_registry.register("jira", "issue", "ai", JiraIssueAIFormatter())
formatter_registry.register("jira", "issue", "rich", JiraIssueRichFormatter())
formatter_registry.register("jira", "issue", "markdown", JiraIssueMarkdownFormatter())
```

**Lookup:**
```python
formatter = formatter_registry.get("ai", plugin="jira", data_type="issue")
return PlainTextResponse(formatter.format(data))
```

### 6. Configuration (lib/config.py)

Credentials loaded from `~/.env.jira`:

**Jira Cloud:**
```bash
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token
```

**Jira Server/DC:**
```bash
JIRA_URL=https://jira.yourcompany.com
JIRA_PERSONAL_TOKEN=your-personal-access-token
```

## Data Flow Patterns

### Pattern 1: Simple GET

```
jira issue PROJ-123
    │
    ▼
bin/jira: ensure_server() + route_request()
    │
    ▼
GET http://127.0.0.1:9200/jira/issue/PROJ-123
    │
    ▼
routes/issues.py: get_issue()
    │
    ▼
Depends(jira) → deps.py: get_client()
    │
    ▼
client.issue("PROJ-123")
    │
    ▼
Jira API → JSON response
    │
    ▼
formatted(data, "ai", "issue")
    │
    ▼
JiraIssueAIFormatter.format(data)
    │
    ▼
PlainTextResponse
```

### Pattern 2: Search with JQL

```
jira search --jql 'project = PROJ AND status != Done'
    │
    ▼
bin/jira: URL-encode JQL with --data-urlencode
    │
    ▼
GET /jira/search?jql=project%20%3D%20PROJ%20AND%20status%20%21%3D%20Done
    │
    ▼
routes/search.py: preprocess_jql()
    │   └─ Converts != to NOT field = (workaround for library bug)
    │
    ▼
client.jql(processed_jql, limit=50)
    │
    ▼
formatted(issues, "ai", "search")
```

### Pattern 3: Write Operation (POST with JSON body)

```
jira comment PROJ-123 --text "Work completed"
    │
    ▼
bin/jira: builds JSON body {"text": "Work completed"}
    │
    ▼
POST /jira/comment/PROJ-123
  Content-Type: application/json
  Body: {"text": "Work completed"}
    │
    ▼
routes/comments.py: add_comment(key, body: AddCommentBody)
    │   Pydantic validates body → AddCommentBody(text="Work completed")
    │
    ▼
client.issue_add_comment(key, body.text)
    │
    ▼
success(result)
```

## Extension Points

### Adding a New Route

```
routes/myfeature.py
        │
        ▼
1. Create router = APIRouter()
2. Define endpoints with @router.get/post/etc
3. Use Depends(jira) for client access
4. Use formatted() for response formatting
        │
        ▼
routes/__init__.py
    1. Import router
    2. Add to create_router()
```

### Adding a New Formatter

```
formatters/myentity.py
        │
        ▼
1. Create classes extending AIFormatter, RichFormatter, MarkdownFormatter
2. Implement format(self, data) method
        │
        ▼
formatters/__init__.py
    1. Import classes
    2. Add to __all__
    3. Register in register_jira_formatters()
```

## Error Handling

All routes use HTTP status code checking via helpers in `response.py`:

```python
from ..response import success, error, get_status_code, is_status

try:
    result = client.issue(key)
    return success(result)
except HTTPError as e:
    if is_status(e, 404):
        return error(f"Issue {key} not found", status=404)
    raise HTTPException(status_code=get_status_code(e) or 500, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

Custom 404 handler in `main.py` provides helpful messages for missing parameters:

```python
ROUTES_REQUIRING_KEY = {
    "/jira/watchers": "watchers/{key} - List watchers for an issue",
    "/jira/comments": "comments/{key} - List comments for an issue",
    ...
}
```

## Security

- Credentials stored in `~/.env.jira` (chmod 600 recommended)
- Server binds to localhost only (`127.0.0.1:9200`)
- No secrets in logs or error messages

## Performance

1. **Persistent server**: FastAPI stays running, only HTTP routing overhead per request
2. **Fresh client per request**: Avoids stale connection issues (~100ms overhead, negligible for CLI)
3. **AI format**: Token-efficient output reduces LLM context usage
4. **JQL preprocessing**: Workarounds for library bugs handled once

## File Structure

```
├── plugin.json                 # Plugin manifest
├── bin/jira                    # Self-bootstrapping CLI wrapper
├── jira/                       # Python package
│   ├── main.py                 # FastAPI app
│   ├── deps.py                 # Dependency injection
│   ├── response.py             # Response formatting + error utilities
│   ├── routes/                 # 20 endpoint modules (Pydantic models for POST/PATCH)
│   ├── formatters/             # Output formatters (ai, rich, markdown)
│   └── lib/                    # Config, client, workflow engine
├── agents/                     # Subagent definitions
│   └── jira-agent.md           # Memory-enabled agent for complex workflows
├── skills/                     # Claude Code skills
│   ├── jira/                   # Main CLI skill + references
│   ├── jira-syntax/            # Wiki markup skill + templates
│   ├── jira-report/            # Multi-ticket analysis (forks to jira-agent)
│   └── jira-bulk/              # Bulk operations (forks to jira-agent)
├── tests/                      # Unit + integration tests
└── pyproject.toml              # Package config
```
