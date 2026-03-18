# Jira Plugin Architecture

How the standalone Jira plugin works, how components connect, and the data flow from CLI to Jira API.

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
│  1. Ensures uv is available                                                │
│  2. Ensures server is running (auto-starts if needed via uv run)           │
│  3. Converts CLI args to HTTP request                                      │
│  4. Routes: jira issue PROJ-123 → GET /jira/issue/PROJ-123                 │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ GET http://127.0.0.1:9200/jira/issue/PROJ-123
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Standalone FastAPI Server (main.py, port 9200)                            │
│  ──────────────────────────────────────────────                            │
│  • Self-contained — no external dependencies beyond pyproject.toml         │
│  • Cached Jira client singleton (initialized at startup)                   │
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
│  • ... 18 route modules total                                              │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Depends(jira) injection
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Dependency Injection (deps.py)                                            │
│  ──────────────────────────────                                            │
│  • Cached Jira client singleton (created once at startup)                  │
│  • User timezone from Jira profile (for worklog timestamps)                │
│  • FastAPI Depends() integration                                           │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ client.issue("PROJ-123")
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  JiraClient (lib/client.py) → extends atlassian-python-api                 │
│  ─────────────────────────────────────────────────                         │
│  • Thin subclass of atlassian.Jira with upstream bug workaround            │
│  • Fixes missing MIME type in multipart attachment uploads                  │
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
# First run: uv installs deps, starts server
jira issue PROJ-123

# Subsequent runs: just routes to running server
jira issue PROJ-123
```

**Key features:**
- Requires `uv` — auto-manages venv and dependencies via `uv run --locked`
- Auto-starts server on first command
- PID file management for server lifecycle
- Graceful shutdown with SIGTERM→SIGKILL fallback
- Port-in-use detection prevents conflicting servers

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
    # Startup: Initialize cached Jira client + user timezone
    init_client()
    yield
    # Shutdown: nothing to clean up (requests.Session handles it)

app = FastAPI(lifespan=lifespan)
app.include_router(create_router(), prefix="/jira")
```

**Endpoints:**
- `/ready` - Liveness probe (used by bin/jira to detect server ready)
- `/` - Basic info
- `/jira/*` - All Jira operations

### 3. Route Modules (routes/*.py)

Each module handles a specific domain:

| Module | Endpoints | Purpose |
|--------|-----------|---------|
| issues.py | `/issue/{key}`, `/show/{key}`, `/create`, `/delete/{key}` | Issue CRUD |
| search.py | `/search` | JQL queries |
| comments.py | `/comments/{key}`, `/comment/{key}`, DELETE `/comment/{key}/{id}` | Comments |
| workflow.py | `/transitions/{key}`, `/transition/{key}` | Status changes |
| watchers.py | `/watchers/{key}`, `/watcher/{key}` | Watchers |
| attachments.py | `/attachments/{key}`, `/attachment/{key}`, DELETE `/attachment/{id}` | File upload/delete |
| links.py | `/links/{key}`, `/linktypes`, `/link`, `/weblink/{key}`, `/weblinks/{key}` | Issue + web links |
| worklogs.py | `/worklogs/{key}`, `/worklog/{key}` | Time tracking |
| projects.py | `/projects`, `/project/{key}` | Projects |
| statuses.py | `/statuses`, `/status/{name}` | Status metadata |
| priorities.py | `/priorities` | Priority metadata |
| components.py | `/components/{project}`, `/component/{id}` | Component CRUD |
| versions.py | `/versions/{project}`, `/version/{id}` | Version/release management |
| agile.py | `/boards`, `/sprints/{board}`, `/sprint/{id}` | Sprints and boards |
| filters.py | `/filters`, `/filter/{id}` | Saved filters |
| fields.py | `/fields`, `/fields/custom` | Field metadata |
| user.py | `/user`, `/user/me` | Current user |
| health.py | `/health` | Health check |
| help.py | `/help`, `/help/{endpoint}` | API docs |

### 4. Dependency Injection (deps.py)

Cached singleton client — initialized once at startup:

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

The `atlassian-python-api` library uses `requests.Session` internally, which handles connection pooling and keep-alive automatically.

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
@register_formatter("jira", "issue", "ai")
class JiraIssueAIFormatter(AIFormatter):
    ...
```

Formatters auto-register when their module is imported. Importing `jira.formatters` in `jira/__init__.py` triggers all decorators.

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
jira issue PROJ-123 --format ai
    │
    ▼
bin/jira: ensure_server() + route_request()
    │
    ▼
GET http://127.0.0.1:9200/jira/issue/PROJ-123?format=ai
    │
    ▼
routes/issues.py: get_issue(key, format, client=Depends(jira))
    │
    ▼
client.issue("PROJ-123")  →  Jira API  →  JSON response
    │
    ▼
formatted(data, "ai", "issue")
    │
    ▼
JiraIssueAIFormatter.format(data)  →  PlainTextResponse
```

### Pattern 2: Write Operation (POST with JSON body)

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
    Pydantic validates body → AddCommentBody(text="Work completed")
    │
    ▼
client.issue_add_comment(key, body.text)
    │
    ▼
success(result)  →  JSONResponse({"success": true, "data": ...})
```

## Error Handling

All routes use the `@jira_error_handler` decorator from `response.py`, which catches HTTPError (404, 409, 403, 400) and Exception automatically:

```python
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

The decorator auto-detects whether the handler has a `format` parameter and returns format-aware errors accordingly.

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

## Upstream Workarounds

### Attachment MIME type (lib/client.py)

`atlassian-python-api` passes file objects to `requests` using the simple form
`files={"file": fobj}`. With `urllib3` 2.x, this no longer auto-sets the per-part
`Content-Type` header, so Jira receives attachments without MIME type metadata.

`JiraClient` subclasses `atlassian.Jira` and overrides `add_attachment_object()` to
use the explicit tuple form `(filename, fobj, content_type)` with MIME type guessed
via `mimetypes.guess_type()`.

**Remove when:** upstream `add_attachment_object()` passes Content-Type in the file tuple.

## Performance

1. **Persistent server**: FastAPI stays running, only HTTP routing overhead per request
2. **Cached singleton client**: Initialized once at startup with connection pooling via `requests.Session`
3. **AI format**: Token-efficient output reduces LLM context usage
4. **JQL preprocessing**: Workarounds for library bugs handled transparently

## File Structure

```
├── plugin.json                 # Plugin manifest
├── bin/jira                    # Self-bootstrapping CLI wrapper (uses uv)
├── jira/                       # Python package
│   ├── main.py                 # FastAPI app
│   ├── deps.py                 # Dependency injection (cached singleton)
│   ├── response.py             # Response formatting + error utilities
│   ├── routes/                 # 18 endpoint modules (Pydantic models for POST/PATCH)
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
├── pyproject.toml              # Package config
└── uv.lock                     # Locked dependencies
```
