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
│  • Manages Jira client singleton                                           │
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
│  • ... 17 route modules total                                              │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Depends(jira) injection
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Dependency Injection (deps.py)                                            │
│  ──────────────────────────────                                            │
│  • Module-level Jira client singleton                                      │
│  • Circuit breaker protection                                              │
│  • Health status tracking                                                  │
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
- Proper URL encoding with `curl --data-urlencode`
- PID file management for server lifecycle

**CLI to HTTP translation:**
```
jira issue PROJ-123 --format ai --expand changelog
  │    │      │          │            │
  │    │      │          │            └─ Query param: expand=changelog
  │    │      │          └─ Query param: format=ai
  │    │      └─ Path segment
  │    └─ Endpoint name
  └─ Plugin prefix

Result: GET /jira/issue/PROJ-123?format=ai&expand=changelog
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
| issues.py | `/issue/{key}`, `/create` | Issue CRUD |
| search.py | `/search` | JQL queries |
| comments.py | `/comments/{key}`, `/comment/{key}` | Comments |
| workflow.py | `/transitions/{key}`, `/transition/{key}` | Status changes |
| watchers.py | `/watchers/{key}`, `/watcher/{key}` | Watchers |
| attachments.py | `/attachments/{key}`, `/attachment/{key}` | Files |
| links.py | `/links/{key}`, `/linktypes` | Issue links |
| worklogs.py | `/worklogs/{key}`, `/worklog/{key}` | Time tracking |
| projects.py | `/projects`, `/project/{key}` | Projects |
| statuses.py | `/statuses`, `/status/{name}` | Status metadata |
| priorities.py | `/priorities` | Priority metadata |
| user.py | `/user/me` | Current user |
| health.py | `/health` | Health check |
| help.py | `/help`, `/help/{endpoint}` | API docs |

### 4. Dependency Injection (deps.py)

Module-level singleton with circuit breaker:

```python
_client = None
_healthy = False
_circuit_state = "closed"
_failure_count = 0

def jira():
    """FastAPI dependency - get Jira client with circuit breaker."""
    if _circuit_state == "open":
        raise HTTPException(503, "Circuit breaker open - Jira unavailable")
    try:
        return get_client()
    except Exception as e:
        _record_failure()
        raise HTTPException(503, f"Jira not connected: {e}")
```

**Circuit breaker states:**
```
closed ──[5 failures]──▶ open ──[30s timeout]──▶ half_open
   ▲                                                  │
   └──────────[success]───────────────────────────────┘
```

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

### Pattern 3: Write Operation

```
jira transition PROJ-123 --transition "In Progress"
    │
    ▼
POST /jira/transition/PROJ-123?transition=In%20Progress
    │
    ▼
routes/workflow.py: transition_issue()
    │
    ├─▶ client.get_issue_transitions("PROJ-123")
    │       │
    │       ▼
    │   Find matching transition by name
    │       │
    │       ▼
    │   (not found?) → formatted_error("Transition not found", ...)
    │
    └─▶ client.set_issue_status_by_transition_id(key, transition_id)
            │
            ▼
        success({"key": "PROJ-123", "transitioned_to": "In Progress"})
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

All routes use consistent error handling via `response.py`:

```python
# Success
return formatted(data, format, "issue")

# Error with hint
return formatted_error("Issue not found", hint="Check issue key", fmt=format, status=404)
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
- Circuit breaker prevents credential stuffing via repeated failures

## Performance

1. **Persistent server**: Connection reuse, no startup overhead per request
2. **Circuit breaker**: Prevents hammering failed API
3. **AI format**: Token-efficient output reduces LLM context usage
4. **JQL preprocessing**: Workarounds for library bugs handled once

## File Structure

```
jira/1.3.0/
├── bin/jira                    # Self-bootstrapping CLI
├── jira/                       # Python package
│   ├── main.py                 # FastAPI app
│   ├── deps.py                 # Dependency injection + circuit breaker
│   ├── response.py             # Response formatting
│   ├── routes/                 # Endpoint handlers
│   ├── formatters/             # Output formatters
│   └── lib/                    # Config, client utilities
├── skills/                     # Claude Code skills
├── tests/                      # Test suite
└── pyproject.toml              # Package config
```
