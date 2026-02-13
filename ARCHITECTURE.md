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
│  • ... 18 route modules total                                              │
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
| attachments.py | `/attachments/{key}`, `/attachment/{key}`, DELETE `/attachment/{id}` | File upload/delete |
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
@register_formatter("jira", "issue", "ai")
class JiraIssueAIFormatter(AIFormatter):
    ...

@register_formatter("jira", "issue", "rich")
class JiraIssueRichFormatter(RichFormatter):
    ...

@register_formatter("jira", "issue", "markdown")
class JiraIssueMarkdownFormatter(MarkdownFormatter):
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
2. Decorate with @register_formatter("jira", "entity", "ai/rich/markdown")
3. Import in formatters/__init__.py (triggers auto-registration)
```

No need to edit `register_jira_formatters()` — it no longer exists.

## Error Handling

All routes use the `@jira_error_handler` decorator from `response.py`, which catches HTTPError (404, 409, 403, 400) and Exception automatically, with format-aware error responses for GET endpoints:

**GET endpoints** (with `format` param):

```python
from ..response import jira_error_handler, formatted

@jira_error_handler(not_found="Issue {key} not found")
@router.get("/issue/{key}")
async def get_issue(
    key: str,
    format: str = Query("json"),
    client=Depends(jira),
):
    """Get issue details by key."""
    data = client.issue(key)
    return formatted(data, format, "issue")
```

**Write endpoints** (POST/PATCH/DELETE without `format` param) use the same decorator:

```python
@jira_error_handler(not_found="Issue {key} not found")
@router.post("/comment/{key}")
async def add_comment(key: str, body: AddCommentBody, client=Depends(jira)):
    result = client.issue_add_comment(key, body.text)
    return success(result)
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

## Upstream Workarounds

### Attachment MIME type (lib/client.py)

`atlassian-python-api` passes file objects to `requests` using the simple form
`files={"file": fobj}`. With `urllib3` 2.x, this no longer auto-sets the per-part
`Content-Type` header, so Jira receives attachments without MIME type metadata —
PDFs render as raw binary, images won't preview, etc.

`JiraClient` subclasses `atlassian.Jira` and overrides `add_attachment_object()` to
use the explicit tuple form `(filename, fobj, content_type)` with MIME type guessed
via `mimetypes.guess_type()`.

**Upstream references:**
- [atlassian-python-api #514](https://github.com/atlassian-api/atlassian-python-api/issues/514) — closed without fix
- [JRACLOUD-72884](https://jira.atlassian.com/browse/JRACLOUD-72884) — Jira confirms attachments without MIME type won't display

**Remove when:** upstream `add_attachment_object()` passes Content-Type in the file tuple.

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
└── pyproject.toml              # Package config
```
