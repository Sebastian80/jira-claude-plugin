# Jira Plugin for AI Tool Bridge

Issue tracking and workflow automation plugin for the AI Tool Bridge daemon.

## Features

- **Issue Operations**: Get, create, update issues
- **Search**: JQL queries with pagination
- **Workflow**: Transitions, status changes
- **Comments & Worklogs**: Time tracking, comments
- **Links**: Issue links, web links
- **Project Data**: Components, versions, metadata

## Architecture

```
jira/
├── plugin.py          # PluginProtocol implementation
├── connector.py       # JiraConnector with circuit breaker
├── deps.py            # FastAPI dependencies
├── response.py        # Response formatting
├── formatters.py      # Rich, AI, Markdown formatters
├── routes/            # FastAPI routers
│   ├── __init__.py    # Combined router
│   └── help.py        # Self-documenting API
├── tools/             # Pydantic Tool classes
│   ├── issues.py      # GetIssue, CreateIssue, UpdateIssue
│   ├── search.py      # SearchIssues (JQL)
│   ├── comments.py    # GetComments, AddComment
│   ├── workflow.py    # GetTransitions, Transition
│   ├── links.py       # Issue/web links
│   └── ...            # Other tools
└── lib/               # Shared utilities
    ├── client.py      # Jira client factory
    └── config.py      # Environment config
```

## Usage

Via CLI (through AI Tool Bridge):
```bash
jira issue PROJ-123
jira search --jql "assignee = currentUser()"
jira transition PROJ-123 --target "In Progress"
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

## Output Formats

| Format | Description |
|--------|-------------|
| `ai` | Token-efficient for LLM consumption (default) |
| `rich` | Colored terminal output |
| `markdown` | Markdown tables |
| `json` | Raw JSON |

## Development

```bash
# Run tests
pytest tests/unit/ -v

# All 71 tests should pass
```

## Tool Pattern

Tools follow the Pydantic-based pattern:

```python
class GetIssue(Tool):
    """Get issue details by key."""

    key: str = Field(..., description="Issue key like PROJ-123")
    format: str = Field("ai", description="Output format")

    class Meta:
        method = "GET"
        path = "/issue/{key}"
        tags = ["issues"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            issue = ctx.client.issue(self.key)
            return formatted(issue, self.format, "issue")
        except Exception as e:
            return ToolResult(error=str(e), status=500)
```

## License

Internal use only.
