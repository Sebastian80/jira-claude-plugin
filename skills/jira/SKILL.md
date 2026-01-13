---
name: jira
description: Use when any ticket key appears (PROJ-123, HMKG-2064) anywhere - conversation, files, git branches, errors. Also for "look up ticket", "find issues", JQL queries, or any Jira/ticket/issue mention.
---

# Jira CLI

Standalone `jira` CLI for all Jira operations. Self-contained FastAPI server.

## The Iron Law

```
TICKET KEY MENTIONED = FETCH IT. NO EXCEPTIONS.
```

If a ticket key (PROJ-123, HMKG-2064) appears anywhere - user message, file, git branch, error - **fetch it with `jira issue KEY`**. Fetching takes 2 seconds. Guessing wastes time.

## Quick Reference

```bash
# Single issue
jira issue PROJ-123                          # Get issue (json format default)
jira issue PROJ-123 --format ai              # Token-efficient for LLMs

# Search
jira search --jql 'assignee = currentUser()' # Use single quotes for JQL

# Workflow
jira transitions PROJ-123                    # List available transitions
jira transition PROJ-123 --target "In Progress"
jira transition PROJ-123 --target "Done" --dryRun  # Preview without executing

# Comments & Time
jira comment PROJ-123 --text "Done"          # Add comment
jira worklog PROJ-123 --timeSpent 2h         # Log time

# Help
jira help                                    # Full command list
jira help search                             # Command-specific help
```

## Output Formats

```bash
--format json      # Default: Raw API response
--format ai        # Token-efficient for LLMs
--format rich      # Terminal colors and panels
--format markdown  # Markdown tables
```

## Creating Issues

```bash
# Basic
jira create --project PROJ --type Task --summary "New task"

# Full example
jira create --project PROJ --type Bug --summary "Fix login" \
  --assignee john --priority High \
  --description "Login fails on mobile"
```

**Parameters:** `--project`, `--type`, `--summary` (required), `--description`, `--priority`, `--labels`, `--assignee`

## Server Management

```bash
jira start      # Start server (auto-starts on first command)
jira stop       # Stop server
jira status     # Show server status
jira restart    # Restart server
jira health     # Check Jira connection
```

## Related Skills

**jira-syntax**: Jira wiki markup (NOT Markdown)
- `*bold*` not `**bold**`
- `h2. Heading` not `## Heading`
- `{code:python}...{code}` not triple backticks

## References

- [commands.md](references/commands.md) - Full command reference
- [jql-quick-reference.md](references/jql-quick-reference.md) - JQL syntax
- [localization.md](references/localization.md) - German/localized status names
- [troubleshooting.md](references/troubleshooting.md) - Common issues

## Authentication

Credentials in `~/.env.jira`:

**Jira Cloud:**
```bash
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
```

**Jira Server/DC:**
```bash
JIRA_URL=https://jira.yourcompany.com
JIRA_PERSONAL_TOKEN=your-personal-access-token
```

Verify with: `jira health`
