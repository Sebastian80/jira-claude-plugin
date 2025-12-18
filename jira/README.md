# Jira Plugin Internals

Internal architecture and component documentation for the `jira/` package.

## Package Structure

```
jira/
├── __init__.py      # Exports JiraPlugin
├── plugin.py        # Plugin entry point, lifecycle management
├── connector.py     # JiraConnector with circuit breaker
├── deps.py          # FastAPI dependency injection
├── response.py      # Response formatting utilities
│
├── tools/           # CLI commands as Pydantic Tool classes
│   ├── __init__.py  # ALL_TOOLS list, exports
│   ├── issues.py    # GetIssue, GetIssues, CreateIssue, UpdateIssue
│   ├── search.py    # SearchIssues (JQL)
│   ├── workflow.py  # GetTransitions, Transition, GetWorkflows
│   ├── comments.py  # GetComments, AddComment
│   ├── worklogs.py  # GetWorklogs, AddWorklog
│   ├── links.py     # GetLinks, CreateIssueLink, CreateWebLink
│   ├── attachments.py
│   ├── watchers.py
│   ├── projects.py
│   ├── components.py
│   ├── versions.py
│   ├── metadata.py  # GetFields, GetPriorities, GetStatuses, GetFilters
│   └── user.py      # GetCurrentUser, GetHealth
│
├── formatters/      # Output formatters (AI, Rich, Markdown)
│   ├── __init__.py  # Registry, registration function
│   ├── base.py      # Base classes, utilities
│   ├── issue.py     # Issue formatters
│   ├── search.py    # Search results formatters
│   └── ...          # Entity-specific formatters
│
├── routes/          # FastAPI routers
│   ├── __init__.py  # create_router() - combines all routes
│   └── help.py      # Self-documenting /help endpoint
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
2. Bridge Plugin Router (toolbus/cli/plugin_router.py)
   Parses args → HTTP request
   GET http://[::1]:9100/jira/issue/PROJ-123?format=ai
          │
          ▼
3. FastAPI Daemon
   Routes to /jira/* router
          │
          ▼
4. Tool Registry (routes/__init__.py)
   register_tools(router, ALL_TOOLS, Depends(jira))
   Matches GET /issue/{key} → GetIssue tool
          │
          ▼
5. Dependency Injection (deps.py)
   jira() → connector_registry.get("jira").client
          │
          ▼
6. Tool Execution (tools/issues.py)
   GetIssue.execute(ctx)
   ctx.client.issue("PROJ-123")
          │
          ▼
7. Jira Connector (connector.py)
   Circuit breaker check → Pass to atlassian.Jira client
          │
          ▼
8. Jira API
   HTTPS request to Jira Cloud/Server
          │
          ▼
9. Response Formatting (response.py)
   formatted(data, "ai", "issue")
   → FormatterRegistry.get("ai", "jira", "issue")
   → JiraIssueAIFormatter.format(data)
          │
          ▼
10. CLI Output
    PlainTextResponse → stdout
```

## Key Components

### plugin.py - Entry Point

```python
class JiraPlugin:
    """Implements PluginProtocol for AI Tool Bridge."""

    @property
    def name(self) -> str: return "jira"

    @property
    def router(self) -> APIRouter:
        return create_router()  # All /jira/* routes

    async def startup(self):
        # Register connector with bridge's global registry
        self._connector_registry.register(self._connector)
        # Establish Jira connection
        await self._connector.connect()

    async def shutdown(self):
        await self._connector.disconnect()
        self._connector_registry.unregister("jira")
```

### connector.py - Resilient API Client

```python
class JiraConnector:
    """Wraps atlassian.Jira with circuit breaker."""

    # Circuit breaker config
    _failure_threshold = 5      # Failures before opening
    _reset_timeout = 30.0       # Seconds until half_open

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

Circuit breaker states:
- `closed`: Normal operation
- `open`: Failing fast, no requests sent
- `half_open`: Testing if service recovered

### deps.py - Dependency Injection

```python
def jira():
    """FastAPI dependency - provides Jira client."""
    connector = connector_registry.get_optional("jira")
    if not connector or not connector.healthy:
        raise HTTPException(503, "Jira not connected")
    return connector.client

# Usage in route registration:
register_tools(router, ALL_TOOLS, client_dependency=Depends(jira))
```

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

### routes/__init__.py - Router Creation

```python
def create_router() -> APIRouter:
    router = APIRouter()

    # Help endpoint (manual route)
    router.include_router(help_router)

    # Auto-generate routes from Tool classes
    register_tools(
        router,
        ALL_TOOLS,
        client_dependency=Depends(jira),
        formatter=formatted,
    )

    return router
```

## Tool Registration

Tools are automatically converted to FastAPI routes:

```python
class GetIssue(Tool):
    key: str = Field(...)           # → Path parameter
    format: str = Field("ai")       # → Query parameter

    class Meta:
        method = "GET"              # → HTTP method
        path = "/issue/{key}"       # → Route path

    async def execute(self, ctx):   # → Route handler
        ...
```

Becomes:
```
GET /jira/issue/{key}?format=ai
```

## Formatter Registration

Formatters are registered by (plugin, data_type, format):

```python
# In formatters/__init__.py

def register_jira_formatters():
    # Issue formatters
    formatter_registry.register("jira", "issue", "ai", JiraIssueAIFormatter())
    formatter_registry.register("jira", "issue", "rich", JiraIssueRichFormatter())

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

## Health Checks

```python
# plugin.py
async def health_check(self) -> dict:
    status = self._connector.status()
    return {
        "status": "healthy" if status["healthy"] else "unhealthy",
        "circuit_state": status["circuit_state"],
        "failure_count": status.get("failure_count", 0),
    }
```

CLI: `jira health`

## Debugging

```bash
# Plugin health
jira health

# Daemon logs
tail -f ~/.local/share/ai-tool-bridge/logs/daemon.log

# Direct API call
curl "http://[::1]:9100/jira/issue/PROJ-123"

# OpenAPI spec
curl "http://[::1]:9100/openapi.json" | jq '.paths | keys'

# Reload after code changes
~/.claude/.../ai-tool-bridge/.venv/bin/bridge reload
```

## See Also

- [../ARCHITECTURE.md](../ARCHITECTURE.md) - System-wide architecture
- [../EXTENDING.md](../EXTENDING.md) - Adding new functionality
- [tools/README.md](tools/README.md) - Tool class patterns
- [formatters/README.md](formatters/README.md) - Formatter system
