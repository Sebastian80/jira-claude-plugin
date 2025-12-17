# Jira Plugin Architecture

## Overview

```
User runs: jira issue PROJ-123
                │
                ▼
┌─────────────────────────────────────┐
│  bin/jira (bash wrapper)            │
│  → bridge jira issue PROJ-123       │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  AI Tool Bridge Daemon (port 9100)  │
│  FastAPI server, plugin host        │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  JiraPlugin (plugin.py)             │
│  - Registers connector on startup   │
│  - Provides router with all routes  │
│  - Handles health checks            │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Tools (tools/*.py)                 │
│  Pydantic classes with execute()    │
│  - GetIssue, Search, Transition...  │
│  - Auto-generate CLI help           │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  JiraConnector (connector.py)       │
│  - Wraps atlassian-python-api       │
│  - Circuit breaker for resilience   │
│  - Auto-reconnect on failure        │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Formatters (formatters/*.py)       │
│  - Transform API responses          │
│  - Formats: json, rich, ai, md      │
└─────────────────────────────────────┘
```

## Directory Structure

```
jira/
├── __init__.py          # Package init, exports JiraPlugin
├── plugin.py            # JiraPlugin class (entry point)
├── connector.py         # JiraConnector (API client wrapper)
├── response.py          # formatted() helper for output
├── deps.py              # FastAPI Depends() injection
│
├── tools/               # Pydantic Tool classes
│   ├── __init__.py      # Exports all tools
│   ├── issues.py        # GetIssue, CreateIssue, UpdateIssue
│   ├── search.py        # Search (JQL)
│   ├── workflow.py      # GetTransitions, Transition
│   ├── comments.py      # GetComments, AddComment
│   ├── worklogs.py      # GetWorklogs, AddWorklog
│   ├── links.py         # GetLinks, CreateIssueLink, CreateWebLink
│   └── ...              # See tools/README.md
│
├── formatters/          # Output formatters
│   ├── __init__.py      # Registry and exports
│   ├── base.py          # Base classes, utilities
│   ├── issue.py         # Issue formatters
│   ├── search.py        # Search result formatters
│   └── ...              # See formatters/README.md
│
├── routes/              # Legacy route helpers
│   └── help.py          # Help text generation
│
└── lib/                 # Shared utilities
    ├── client.py        # Client helpers
    ├── config.py        # Configuration loading
    ├── output.py        # Output utilities
    └── workflow.py      # Workflow helpers
```

## Plugin Lifecycle

### 1. Discovery

Bridge scans for plugins via `manifest.json`:

```
skills/jira/manifest.json
    ↓
{
  "entry_point": "jira:JiraPlugin",
  "python_path": ["../.."],
  "dependencies": ["atlassian-python-api>=4.0", "rich>=13.0.0"]
}
```

### 2. Dependency Loading

```
manifest.json declares deps
    ↓
bridge deps sync
    ↓
uv pip install into bridge venv
    ↓
Hash stored to detect changes
```

Check status: `~/.claude/.../ai-tool-bridge/.venv/bin/bridge deps status`

Dependencies are installed into the bridge's shared venv, not per-plugin.
When manifest changes, `bridge deps sync` detects via hash comparison.

### 3. Plugin Instantiation

```python
# Bridge does this:
from jira import JiraPlugin
plugin = JiraPlugin(bridge_context={"connector_registry": registry})
```

### 4. Startup

```python
async def startup(self):
    # 1. Register connector with bridge
    self._connector_registry.register(self._connector)

    # 2. Connect to Jira API
    await self._connector.connect()
```

### 5. Request Handling

```
CLI: jira issue PROJ-123
    ↓
Bridge routes to: GET /jira/issue/PROJ-123
    ↓
Router matches Tool class: GetIssue
    ↓
Tool.execute(ctx) runs with:
    - ctx.client = Jira API client
    - ctx.params = parsed CLI args
    ↓
Returns ToolResult or formatted output
```

### 6. Shutdown

```python
async def shutdown(self):
    await self._connector.disconnect()
    self._connector_registry.unregister("jira")
```

## Key Components

### JiraConnector (connector.py)

Wraps the `atlassian-python-api` Jira client with:

- **Circuit breaker**: Prevents hammering failed API
- **Auto-reconnect**: Retries on transient failures
- **Health tracking**: Exposes connection status

```python
connector = JiraConnector()
await connector.connect()  # Reads ~/.env.jira

# Access underlying client
connector.client.issue("PROJ-123")

# Check health
connector.healthy  # bool
connector.status()  # {"healthy": bool, "circuit_state": str}
```

### Tools (tools/*.py)

Pydantic classes that define CLI commands. See `tools/README.md`.

```python
class GetIssue(Tool):
    key: str = Field(..., description="Issue key")

    class Meta:
        method = "GET"
        path = "/issue/{key}"

    async def execute(self, ctx: ToolContext) -> Any:
        issue = ctx.client.issue(self.key)
        return formatted(issue, self.format, "issue")
```

### Formatters (formatters/*.py)

Transform API responses to different output formats. See `formatters/README.md`.

```python
# In tool:
return formatted(data, "ai", "issue")

# Looks up: formatter_registry.get("jira", "issue", "ai")
# Returns: JiraIssueAIFormatter().format(data)
```

## Configuration

Credentials in `~/.env.jira`:

```bash
# Jira Cloud
JIRA_URL=https://company.atlassian.net
JIRA_USERNAME=email@example.com
JIRA_API_TOKEN=your-api-token

# OR Jira Server/DC
JIRA_URL=https://jira.company.com
JIRA_PERSONAL_TOKEN=your-pat
```

Loaded by `lib/config.py` on connector startup.

## Adding New Functionality

### New Tool

1. Create class in `tools/<category>.py`
2. Export in `tools/__init__.py`
3. Done - auto-registered, CLI help auto-generated

### New Formatter

1. Create class in `formatters/<entity>.py`
2. Register in `formatters/__init__.py` → `register_jira_formatters()`
3. Use via `formatted(data, format_name, entity_type)`

## Testing

```bash
cd ~/.claude/plugins/marketplaces/sebastian-marketplace/plugins/jira

# Run all tests
uv run pytest tests/ -v

# Run specific category
uv run pytest tests/unit/ -v
uv run pytest tests/routes/ -v
```

## Debugging

```bash
# Check plugin health
jira health

# View daemon logs
tail -f ~/.local/share/ai-tool-bridge/logs/daemon.log

# Direct API test
curl -s "http://[::1]:9100/jira/issue/PROJ-123"

# Reload plugin after code changes
~/.claude/.../ai-tool-bridge/.venv/bin/bridge reload
```
