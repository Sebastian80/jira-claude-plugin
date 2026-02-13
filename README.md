# Jira CLI for Claude Code

Standalone Jira CLI plugin for Claude Code. Self-contained FastAPI server with full issue tracking and workflow automation.

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────┐
│  Claude / User  │────▶│  bin/jira          │────▶│  Jira API   │
│                 │◀────│  (auto-start srv)  │◀────│  Cloud/DC   │
└─────────────────┘     └───────────────────┘     └─────────────┘
                                │
                                ▼
                       ┌───────────────────┐
                       │  FastAPI server    │
                       │  (port 9200)       │
                       └───────────────────┘
```

## Quick Start

```bash
# First run auto-creates venv and starts server
jira issue PROJ-123

# Search with JQL
jira search --jql 'assignee = currentUser()'

# Transition an issue
jira transition PROJ-123 --target "In Progress"

# Comments
jira comment PROJ-123 --text "Work completed"
jira comment PROJ-123 12345 -X DELETE

# Full command list
jira help
```

## Features

| Category | Capabilities |
|----------|--------------|
| **Issues** | Get, create, update, delete issues |
| **Search** | JQL queries with pagination |
| **Workflow** | Smart multi-step transitions with path-finding |
| **Comments** | List, add, delete comments |
| **Time Tracking** | Worklogs with time format validation |
| **Links** | Issue links, web links |
| **Attachments** | List, upload (multi-file), delete attachments |
| **Watchers** | List, add, remove watchers |
| **Sprints** | Boards, sprints, sprint issue management |
| **Project Data** | Components, versions, filters, priorities, statuses |
| **Help** | Self-describing API docs from OpenAPI spec |

## Output Formats

All commands support `--format`:

| Format | Use Case |
|--------|----------|
| `json` | Raw API response (default) |
| `ai` | Token-efficient for LLM consumption |
| `rich` | Colored terminal output |
| `markdown` | Tables for docs and PRs |

```bash
jira issue PROJ-123 --format ai
jira issue PROJ-123 --format rich
jira search --jql 'project = PROJ' --format markdown
```

## Configuration

Create `~/.env.jira`:

**Jira Cloud:**
```bash
JIRA_URL=https://company.atlassian.net
JIRA_USERNAME=email@example.com
JIRA_API_TOKEN=your-token
```

**Jira Server/DC:**
```bash
JIRA_URL=https://jira.company.com
JIRA_PERSONAL_TOKEN=your-pat
```

Verify with: `jira health`

## Server Management

```bash
jira start      # Start server (auto-starts on first command)
jira stop       # Stop server
jira status     # Show server status
jira restart    # Restart server
jira logs       # Tail server logs
jira health     # Check Jira connection
```

## Plugin Structure

```
├── plugin.json            # Plugin manifest
├── bin/jira               # Self-bootstrapping CLI wrapper
├── jira/                  # FastAPI server
│   ├── main.py            # Server entry point
│   ├── deps.py            # Dependency injection
│   ├── response.py        # Response formatting + error utilities
│   ├── routes/            # 18 endpoint modules
│   ├── formatters/        # Output formatters (ai, rich, markdown)
│   └── lib/               # Config, JiraClient (Jira subclass), workflow engine
├── agents/
│   └── jira-agent.md      # Subagent for complex workflows (memory-enabled)
├── skills/
│   ├── jira/              # Main CLI skill + references
│   ├── jira-syntax/       # Wiki markup skill + templates
│   ├── jira-report/       # Multi-ticket analysis (forks to jira-agent)
│   └── jira-bulk/         # Bulk operations (forks to jira-agent)
├── tests/                 # Unit + integration tests
├── pyproject.toml         # Python package config
└── pytest.ini             # Test config
```

## API Design

- **GET/DELETE** endpoints use query parameters
- **POST/PATCH** endpoints use JSON request bodies (Pydantic models)
- Error handling via `@jira_error_handler` decorator (catches HTTPError by status code)
- All endpoints return `{"success": true, "data": ...}` or `{"success": false, "error": ...}`

## Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and data flow |
| [EXTENDING.md](EXTENDING.md) | Guide to adding new functionality |
| `jira help` | Live API documentation from OpenAPI spec |

## Development

```bash
# Run tests (from plugin root)
uv run pytest tests/ -v

# Restart server after code changes
jira restart
```

## License

MIT
