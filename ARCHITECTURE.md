# Jira Plugin Architecture

Deep dive into how the Jira plugin works, how components connect, and the data flow from CLI to Jira API.

## System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              USER / AI AGENT                               │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ jira issue PROJ-123
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  bin/jira (Bash wrapper)                                                   │
│  ─────────────────────────                                                 │
│  Forwards all args to: bridge jira $@                                      │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ bridge jira issue PROJ-123
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  AI Tool Bridge CLI (plugin_router.py)                                     │
│  ─────────────────────────────────────                                     │
│  1. Parses args: plugin=jira, path=/issue/PROJ-123                         │
│  2. Detects HTTP method from OpenAPI spec (GET)                            │
│  3. Converts --flags to query params                                       │
│  4. Auto-starts daemon if not running                                      │
│  5. Sends HTTP request to daemon                                           │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ GET http://[::1]:9100/jira/issue/PROJ-123
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  AI Tool Bridge Daemon (FastAPI on port 9100)                              │
│  ─────────────────────────────────────────────                             │
│  • Hosts plugins as sub-routers                                            │
│  • Manages plugin lifecycle (startup/shutdown)                             │
│  • Maintains connector registry                                            │
│  • Serves OpenAPI documentation                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Routes to /jira/* router
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  JiraPlugin (plugin.py)                                                    │
│  ──────────────────────                                                    │
│  • Implements PluginProtocol                                               │
│  • Creates JiraConnector                                                   │
│  • Provides combined router                                                │
│  • Manages connector lifecycle                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Router matches GET /issue/{key}
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  ToolRegistry (toolbus/tools/registry.py)                                  │
│  ────────────────────────────────────────                                  │
│  • Auto-generated route from GetIssue Tool class                           │
│  • Validates params via Pydantic                                           │
│  • Injects client via Depends(jira)                                        │
│  • Calls Tool.execute(ctx)                                                 │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ GetIssue.execute(ctx)
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  GetIssue Tool (tools/issues.py)                                           │
│  ───────────────────────────────                                           │
│  • ctx.client = Jira API client                                            │
│  • Calls ctx.client.issue(key)                                             │
│  • Returns formatted(data, format, "issue")                                │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ ctx.client.issue("PROJ-123")
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  JiraConnector (connector.py)                                              │
│  ────────────────────────────                                              │
│  • Wraps atlassian-python-api Jira client                                  │
│  • Circuit breaker protection                                              │
│  • Health monitoring                                                       │
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
│  • Looks up: jira:issue:ai formatter                                       │
│  • JiraIssueAIFormatter.format(data)                                       │
│  • Returns token-efficient structured text                                 │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ PlainTextResponse
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Back through the stack to CLI output                                      │
└────────────────────────────────────────────────────────────────────────────┘
```

## Component Deep Dive

### 1. Plugin Entry Point (plugin.py)

The plugin implements `PluginProtocol` required by AI Tool Bridge:

```python
class JiraPlugin:
    @property
    def name(self) -> str: return "jira"
    @property
    def router(self) -> APIRouter: return create_router()

    async def startup(self):
        # 1. Register connector with bridge
        self._connector_registry.register(self._connector)
        # 2. Connect to Jira
        await self._connector.connect()

    async def shutdown(self):
        await self._connector.disconnect()
        self._connector_registry.unregister("jira")
```

**Key responsibilities:**
- Provides plugin metadata (name, version, description)
- Creates and configures the JiraConnector
- Returns the FastAPI router with all endpoints
- Manages lifecycle (startup connects, shutdown disconnects)

### 2. Connector (connector.py)

Wraps the `atlassian-python-api` Jira client with resilience patterns:

```python
class JiraConnector:
    # Circuit breaker states
    _circuit_state: "closed" | "open" | "half_open"
    _failure_count: int
    _failure_threshold: int = 5
    _reset_timeout: float = 30.0

    @property
    def client(self):
        if self.circuit_state == "open":
            raise RuntimeError("Circuit breaker open")
        return self._client

    def _record_failure(self):
        self._failure_count += 1
        if self._failure_count >= self._failure_threshold:
            self._circuit_state = "open"
```

**Circuit breaker flow:**
```
closed ──[5 failures]──▶ open ──[30s timeout]──▶ half_open
   ▲                                                  │
   └──────────[success]───────────────────────────────┘
```

### 3. Tools Framework (toolbus/tools/)

Tools are Pydantic models that define CLI commands:

```python
class GetIssue(Tool):
    """Get issue details by key."""

    # Pydantic fields become CLI params
    key: str = Field(..., description="Issue key like PROJ-123")
    fields: str | None = Field(None, description="Comma-separated fields")
    format: str = Field("ai", description="Output format")

    class Meta:
        method = "GET"              # HTTP method
        path = "/issue/{key}"       # URL path ({key} from field)
        tags = ["issues"]           # OpenAPI grouping

    async def execute(self, ctx: ToolContext) -> Any:
        issue = ctx.client.issue(self.key)
        return formatted(issue, self.format, "issue")
```

**Auto-generation magic:**

The `ToolRegistry` reads Tool classes and:
1. Extracts fields → FastAPI Query/Path parameters
2. Extracts Meta.path → Route path
3. Extracts docstring → OpenAPI documentation
4. Builds endpoint function with proper signature
5. Registers route on FastAPI router

```
Tool class                    Generated endpoint
──────────────────────────────────────────────────────────────
GetIssue                  →   GET /issue/{key}?fields=&format=
  key: str                    Path parameter (required)
  fields: str | None          Query parameter (optional)
  format: str = "ai"          Query parameter (default: ai)
```

### 4. Formatter System (formatters/)

Transforms API responses into different output formats:

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
```

**Lookup:**
```python
# In response.py
formatter = formatter_registry.get("ai", plugin="jira", data_type="issue")
# Returns JiraIssueAIFormatter
```

### 5. Dependency Injection (deps.py)

FastAPI dependencies provide the Jira client:

```python
def jira():
    """Get Jira client from connector registry."""
    connector = connector_registry.get_optional("jira")
    if connector is None:
        raise HTTPException(503, "Jira connector not registered")
    if not connector.healthy:
        raise HTTPException(503, f"Jira not connected (circuit: {connector.circuit_state})")
    return connector.client
```

Used in route registration:
```python
register_tools(router, ALL_TOOLS, client_dependency=Depends(jira))
```

### 6. CLI Routing (toolbus/cli/plugin_router.py)

Converts CLI args to HTTP requests:

```
jira issue PROJ-123 --format rich --expand changelog
  │    │      │          │            │
  │    │      │          │            └─ Query param: expand=changelog
  │    │      │          └─ Query param: format=rich
  │    │      └─ Path segment
  │    └─ Path segment
  └─ Plugin name

Result: GET /jira/issue/PROJ-123?format=rich&expand=changelog
```

**Method detection:**
1. Fetch OpenAPI spec from daemon
2. Match path pattern
3. If multiple methods available, use params to decide
4. Fallback: heuristics based on param names

## Data Flow Patterns

### Pattern 1: Simple GET

```
jira issue PROJ-123
    │
    ▼
GET /jira/issue/PROJ-123
    │
    ▼
GetIssue.execute(ctx)
    │
    ▼
ctx.client.issue("PROJ-123")
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
PlainTextResponse("ISSUE: PROJ-123\nstatus: Open\n...")
```

### Pattern 2: Bulk Fetch (Parallel)

```
jira issues HMKG-1,HMKG-2,HMKG-3
    │
    ▼
GET /jira/issues?keys=HMKG-1,HMKG-2,HMKG-3
    │
    ▼
GetIssues.execute(ctx)
    │
    ├───────────────┬───────────────┐
    ▼               ▼               ▼
asyncio.to_thread  asyncio.to_thread  asyncio.to_thread
fetch_one(HMKG-1)  fetch_one(HMKG-2)  fetch_one(HMKG-3)
    │               │               │
    └───────────────┴───────────────┘
                    │
                    ▼
            asyncio.gather()
                    │
                    ▼
            Aggregate results
                    │
                    ▼
            formatted(response, "ai", "search")
```

### Pattern 3: Write Operation

```
jira transition PROJ-123 --transition "In Progress"
    │
    ▼
POST /jira/transition/PROJ-123?transition=In%20Progress
    │
    ▼
Transition.execute(ctx)
    │
    ├─▶ ctx.client.get_issue_transitions("PROJ-123")
    │       │
    │       ▼
    │   Find matching transition ID
    │       │
    │       ▼
    │   (not found?) → ToolResult(error="...", status=400)
    │
    └─▶ ctx.client.set_issue_status_by_transition_id(key, id)
            │
            ▼
        ToolResult(data={"key": "PROJ-123", "transition": "In Progress"})
```

## Extension Points

### Adding a New Tool

```
tools/myfeature.py
        │
        ▼
class MyFeature(Tool):
    # 1. Define fields (become CLI params)
    # 2. Define Meta (path, method)
    # 3. Implement execute()
        │
        ▼
tools/__init__.py
    ALL_TOOLS.append(MyFeature)
        │
        ▼
Auto-registered on next daemon restart
```

### Adding a New Formatter

```
formatters/myentity.py
        │
        ▼
class MyEntityAIFormatter(AIFormatter):
    def format(self, data): ...
        │
        ▼
formatters/__init__.py
    1. Import class
    2. Add to __all__
    3. Register in register_jira_formatters()
```

### Adding a New Entity Type

Full workflow for adding support for a new Jira entity:

```
1. tools/newentity.py
   └─ GetNewEntity, CreateNewEntity, etc.

2. formatters/newentity.py
   └─ NewEntityAIFormatter, NewEntityRichFormatter

3. formatters/__init__.py
   └─ Import and register formatters

4. tools/__init__.py
   └─ Add to ALL_TOOLS

5. skills/jira/references/commands.md
   └─ Document new commands

6. tests/routes/test_newentity.py
   └─ Add route tests
```

## Configuration Loading

```
~/.env.jira
     │
     ▼
lib/config.py
     │
     ├─ JIRA_URL=...
     ├─ JIRA_USERNAME=... (Cloud)
     ├─ JIRA_API_TOKEN=... (Cloud)
     └─ JIRA_PERSONAL_TOKEN=... (Server/DC)
     │
     ▼
lib/client.py: get_jira_client()
     │
     ├─ Detect Cloud vs Server/DC
     ├─ Create atlassian.Jira instance
     └─ Return configured client
```

## Error Handling

```
Exception Type                Handler Location              Result
────────────────────────────────────────────────────────────────────
ValidationError               ToolRegistry                  422 + field errors
HTTPException                 FastAPI                       Specified status
JiraConnector circuit open    deps.py                       503 + circuit state
Jira API 404                  Tool.execute()                404 + "not found"
Jira API 401/403              Tool.execute()                401/403 + message
Generic Exception             ToolRegistry                  500 + error message
```

## Performance Considerations

1. **Parallel bulk fetch**: GetIssues uses asyncio.gather() with thread pool
2. **Circuit breaker**: Prevents hammering failed API
3. **Daemon architecture**: Persistent connection, no auth overhead per request
4. **AI format**: Token-efficient output reduces LLM context usage
5. **IPv6 loopback**: Bypasses security software that intercepts IPv4 localhost

## Security

- Credentials stored in `~/.env.jira` (chmod 600 recommended)
- Daemon binds to loopback only (`[::1]:9100`)
- No secrets in logs or error messages
- Circuit breaker prevents credential stuffing via repeated failures
