# Jira Plugin for AI Tool Bridge

**Version 1.2.0** | Issue tracking and workflow automation for AI agents.

## Overview

A plugin that enables AI agents to interact with Jira through a unified CLI interface. Designed for token-efficient communication with LLMs while providing rich terminal output for humans.

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────┐
│  Claude/AI      │────▶│  AI Tool Bridge   │────▶│  Jira API   │
│  Agent          │◀────│  (FastAPI daemon) │◀────│  Cloud/DC   │
└─────────────────┘     └───────────────────┘     └─────────────┘
        │                        │
        │                        ▼
        │               ┌───────────────────┐
        └──────────────▶│  jira CLI         │
                        │  (thin wrapper)   │
                        └───────────────────┘
```

## Quick Start

```bash
# Get an issue (AI-optimized format by default)
jira issue PROJ-123

# Bulk fetch multiple issues (parallel, fast)
jira issues HMKG-1,HMKG-2,HMKG-3

# Search with JQL
jira search --jql 'assignee = currentUser()'

# Transition an issue
jira transition PROJ-123 --transition "In Progress"

# Add a comment
jira comment PROJ-123 --body "Work completed"

# Full command list
jira --help
```

## Features

| Category | Capabilities |
|----------|--------------|
| **Issues** | Get, create, update, bulk fetch (parallel) |
| **Search** | JQL queries with pagination |
| **Workflow** | Transitions, status changes |
| **Comments** | List, add comments |
| **Time Tracking** | Worklogs, time spent |
| **Links** | Issue links, web links |
| **Project Data** | Components, versions, metadata |

## Output Formats

| Format | Use Case | Example |
|--------|----------|---------|
| `ai` | LLM consumption (default) | Token-efficient structured text |
| `rich` | Human terminal | Colored panels, tables, icons |
| `markdown` | Documentation | Markdown tables |
| `json` | Scripts/automation | Raw API response |

```bash
jira issue PROJ-123 --format ai       # Default
jira issue PROJ-123 --format rich     # Terminal colors
jira issue PROJ-123 --format json     # Raw JSON
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

## Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Deep dive into component relationships |
| [EXTENDING.md](EXTENDING.md) | Guide to adding new functionality |
| [jira/README.md](jira/README.md) | Plugin internals and lifecycle |
| [jira/tools/README.md](jira/tools/README.md) | Tool class patterns |
| [jira/formatters/README.md](jira/formatters/README.md) | Output formatting system |

## Project Structure

```
jira-plugin/
├── README.md              # This file
├── ARCHITECTURE.md        # How everything connects
├── EXTENDING.md           # Adding new functionality
├── bin/
│   └── jira               # CLI wrapper script
├── jira/                  # Main package
│   ├── plugin.py          # Entry point, lifecycle
│   ├── connector.py       # Jira API client wrapper
│   ├── deps.py            # FastAPI dependencies
│   ├── response.py        # Response formatting
│   ├── tools/             # CLI commands as Tool classes
│   ├── formatters/        # Output formatters
│   ├── routes/            # Help endpoint
│   └── lib/               # Shared utilities
├── skills/                # Claude Code skills
│   ├── jira/              # Main Jira skill
│   └── jira-syntax/       # Wiki markup skill
└── tests/                 # Test suite
```

## Development

```bash
cd ~/.claude/plugins/marketplaces/sebastian-marketplace/plugins/jira

# Run tests
uv run pytest tests/ -v

# Reload plugin after changes
~/.claude/.../ai-tool-bridge/.venv/bin/bridge reload

# Check plugin health
jira health
```

## Version History

- **1.2.0**: Bulk issue fetch with parallel execution, field validation, linked issues expansion
- **1.1.0**: User/health formatters, registry fix, route tests
- **1.0.0**: Initial release

## License

Internal use only.
