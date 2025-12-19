# Jira CLI for Claude Code

**Version 2.0.0** | Standalone Jira CLI for issue tracking and workflow automation.

## Overview

A self-contained Jira CLI that runs as a local FastAPI server. Designed for token-efficient communication with LLMs while providing rich terminal output for humans.

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────┐
│  Claude/AI      │────▶│  bin/jira         │────▶│  Jira API   │
│  Agent          │◀────│  (auto-start srv) │◀────│  Cloud/DC   │
└─────────────────┘     └───────────────────┘     └─────────────┘
                                │
                                ▼
                       ┌───────────────────┐
                       │  FastAPI server   │
                       │  (port 9200)      │
                       └───────────────────┘
```

## Quick Start

```bash
# First run auto-creates venv and starts server
jira issue PROJ-123

# Search with JQL
jira search --jql 'assignee = currentUser()'

# Transition an issue
jira transition PROJ-123 --transition "In Progress"

# Add a comment
jira comment PROJ-123 --body "Work completed"

# Full command list
jira help
```

## Features

| Category | Capabilities |
|----------|--------------|
| **Issues** | Get, create, update issues |
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

## Server Management

```bash
jira start      # Start server (background)
jira stop       # Stop server
jira status     # Show server status
jira restart    # Restart server
jira logs       # Tail server logs
jira health     # Check Jira connection
```

## Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Deep dive into standalone architecture |
| [EXTENDING.md](EXTENDING.md) | Guide to adding new functionality |

## Project Structure

```
jira/
├── README.md              # This file
├── ARCHITECTURE.md        # How everything connects
├── EXTENDING.md           # Adding new functionality
├── bin/
│   └── jira               # Self-bootstrapping CLI wrapper
├── jira/                  # Main Python package
│   ├── main.py            # FastAPI server entry point
│   ├── deps.py            # Dependency injection
│   ├── response.py        # Response formatting
│   ├── routes/            # Endpoint handlers
│   ├── formatters/        # Output formatters
│   └── lib/               # Config, client utilities
├── skills/                # Claude Code skills
│   ├── jira/              # Main Jira skill
│   └── jira-syntax/       # Wiki markup skill
└── tests/                 # Test suite
```

## Development

```bash
# Run tests
cd /path/to/jira-plugin
pytest tests/ -v

# Restart server after changes
jira restart

# Check server health
jira health
```

## Version History

- **2.0.0**: Standalone architecture - no bridge dependency, self-bootstrapping CLI
- **1.2.0**: Bulk issue fetch with parallel execution, field validation
- **1.1.0**: User/health formatters, registry fix, route tests
- **1.0.0**: Initial release

## License

MIT
