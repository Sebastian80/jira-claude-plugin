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

## Usage

```bash
jira issue PROJ-123                          # Get issue (default: ai format)
jira search --jql 'assignee = currentUser()' # Search (use single quotes for JQL)
jira transition PROJ-123 --transition "In Progress"
jira comment PROJ-123 --body "Done"
jira worklog PROJ-123 --timeSpent 2h
jira --help                                  # Full command list
```

## Output Formats

```bash
--format ai        # Default: token-efficient
--format rich      # Terminal colors
--format markdown  # Tables
--format json      # Raw API response
```

## Related Skills

**jira-syntax**: Jira wiki markup (NOT Markdown): `*bold*`, `h2. Heading`, `{code:python}...{code}`

## References

- [commands.md](references/commands.md) - Full command reference
- [jql-quick-reference.md](references/jql-quick-reference.md) - JQL syntax
- [localization.md](references/localization.md) - German/localized status names
- [troubleshooting.md](references/troubleshooting.md) - Common issues

