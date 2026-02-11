---
name: jira
description: Use when any ticket key appears (format PROJECTKEY-NUMBER, e.g., OROSPD-589, HMKG-2064, XX-12) anywhere - conversation, files, git branches, errors. Also for "look up ticket", "find issues", JQL queries, or any Jira/ticket/issue mention.
---

# Jira CLI

Standalone `jira` CLI for all Jira operations. Self-contained FastAPI server.

## The Iron Law

```
TICKET KEY MENTIONED = FETCH IT. NO EXCEPTIONS.
```

If a ticket key (format PROJECTKEY-NUMBER, e.g., OROSPD-589, HMKG-2064, XX-12) appears anywhere - user message, file, git branch, error - **fetch it with `jira issue KEY`**. Fetching takes 2 seconds. Guessing wastes time.

## Context Management

**Simple lookups** (single ticket, quick status check): Handle directly with commands below.

**Complex workflows** use dedicated skills that fork to `jira-agent` with isolated context:
- **`/jira-report`** - Multi-ticket analysis, sprint reviews, reporting, dependency analysis
- **`/jira-bulk`** - Bulk transitions or updates across multiple tickets

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
jira comment PROJ-123 12345 -X DELETE        # Delete comment by ID
jira worklog PROJ-123 --timeSpent 2h         # Log time

# Attachments
jira attachments PROJ-123                    # List attachments
jira attachment PROJ-123 --file report.pdf   # Upload file
jira attachment PROJ-123 --file a.pdf --file b.png  # Upload multiple
jira attachment 12345 -X DELETE              # Delete attachment

# Help
jira help                                    # Full command list
jira help search                             # Command-specific help
```

## Output Formats

```bash
--format json      # Default. Raw API response — use when parsing specific fields
--format ai        # Token-efficient summaries — use for analysis and reporting
--format rich      # Terminal colors and panels — use for human-readable output
--format markdown  # Markdown tables — use for pasting into docs or PRs
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

## Writing Content for Jira

Before creating issues or comments with complex formatting:

1. **Use jira-syntax skill** for wiki markup reference
2. **Use templates**: Bug reports, feature requests with proper Jira formatting
3. **Validate syntax** before submitting

**Example workflow:**
```bash
# Format description with Jira wiki markup, then create issue
jira create --project PROJ --type Bug --summary "Login fails" \
  --description "h2. Steps to Reproduce
* Step 1
* Step 2

h2. Expected
Login succeeds

h2. Actual
{color:red}Error 500{color}"
```

**Common syntax reminders:**
- Headings: `h2. Title` (NOT `## Title`)
- Bold: `*text*` (NOT `**text**`)
- Code: `{code:python}...{code}` (NOT triple backticks)
- Links: `[text|url]` (NOT `[text](url)`)

## Gotchas

- Implementation summaries go in **comments** (`jira comment`), NOT in the description field
- Never write to two tickets simultaneously — parallel writes cause data corruption
- After any write operation, re-fetch the ticket to verify the content was placed correctly
- Never use temp files for Jira content — pipe directly to avoid collisions

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
