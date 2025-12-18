---
name: jira
description: >
  MANDATORY when any ticket key appears (PROJ-123, HMKG-2064, etc.) - fetch it immediately.
  Use for: (1) Any ticket/issue key mentioned anywhere - in conversation, files, git branches, errors,
  (2) "look up", "get", "read", "check", "what's the status of" + ticket reference,
  (3) Searching issues (JQL, "find tickets", "open bugs"),
  (4) Creating, updating, or transitioning tickets,
  (5) Adding comments or logging work time,
  (6) Any mention of "Jira", "ticket", "issue".
  Supports Jira Cloud and Server/Data Center.
---

# Jira Communication

Unified `jira` CLI for all Jira operations via AI Tool Bridge daemon.

## The Iron Law

```
TICKET KEY MENTIONED = FETCH IT. NO EXCEPTIONS.
```

If a ticket key (PROJ-123, HMKG-2064) appears anywhere - user message, file, git branch, error - **fetch it with `jira issue KEY`**. Fetching takes 2 seconds. Guessing wastes time.

## Quick Reference

```bash
# Single issue
jira issue PROJ-123                          # Get issue (ai format)
jira issue PROJ-123 --include-links          # Include linked issues
jira issue PROJ-123 --expand changelog       # Include change history

# Bulk fetch (parallel, fast)
jira issues PROJ-1,PROJ-2,PROJ-3             # Multiple issues at once

# Search
jira search --jql 'assignee = currentUser()' # Use single quotes for JQL

# Workflow
jira transitions PROJ-123                    # List available transitions
jira transition PROJ-123 --transition "In Progress"

# Comments & Time
jira comment PROJ-123 --body "Done"          # Add comment
jira worklog PROJ-123 --timeSpent 2h         # Log time

# Help
jira --help                                  # Full command list
jira help search                             # Command-specific help
```

## Output Formats

```bash
--format ai        # Default: token-efficient for LLMs
--format rich      # Terminal colors and panels
--format markdown  # Markdown tables
--format json      # Raw API response
```

## Creating Issues

```bash
# Basic
jira create --project PROJ --type Task --summary "New task"

# With sprint (use sprint ID)
jira create --project PROJ --type Task --summary "Task" --sprint 901

# Full example
jira create --project PROJ --type Bug --summary "Fix login" \
  --assignee john --priority High --sprint 901 \
  --components "Backend" --fixVersions "v2.0" --duedate 2025-12-31
```

**Parameters:** `--project`, `--type`, `--summary` (required), `--description`, `--priority`, `--labels`, `--assignee`, `--sprint`, `--components`, `--fixVersions`, `--duedate`, `--parent`

## v1.2.0 Features

### Bulk Fetch

Fetch multiple issues in parallel:
```bash
jira issues HMKG-1,HMKG-2,HMKG-3
jira issues "HMKG-1 HMKG-2 HMKG-3"
```

### Linked Issues

Include linked issue summaries:
```bash
jira issue PROJ-123 --include-links
```

### Field Validation

Warns about invalid field names:
```bash
jira issue PROJ-123 --fields summary,foobar
# WARNING: Unknown fields (may be custom): foobar
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

Verify with: `jira user me`
