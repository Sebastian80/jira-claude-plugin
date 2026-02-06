# Jira CLI Command Reference

Full command reference. Use `jira --help` for latest.

## Issues

```bash
# Single issue
jira issue PROJ-123                           # Get issue details
jira issue PROJ-123 --fields summary,status   # Specific fields only
jira issue PROJ-123 --expand changelog        # Include change history
jira issue PROJ-123 --include-links           # Include linked issues

# Bulk fetch - use search instead
jira search --jql 'key in (PROJ-1, PROJ-2, PROJ-3)'

# Create issue
jira create --project PROJ --type Task --summary "New task"
jira create --project PROJ --type Bug --summary "Bug" --sprint 901
jira create --project PROJ --type Story --summary "Story" \
  --assignee john --priority High --duedate 2025-12-31
jira create --project PROJ --type Task --summary "Task" \
  --components "Backend,API" --fixVersions "v2.0"

# Update issue
jira update PROJ-123 --summary "Updated title"
jira update PROJ-123 --assignee jane --priority Low
jira update PROJ-123 --description "New description"
```

## Search

```bash
jira search --jql 'assignee = currentUser()'
jira search --jql 'project = PROJ' --maxResults 50
jira search --jql 'status not in (Done, Closed)'
```

**Note:** Use single quotes for JQL to avoid bash history expansion.

## Transitions

```bash
jira transitions PROJ-123                     # List available transitions
jira transition PROJ-123 --target "In Progress"
jira transition PROJ-123 --target "Done"
```

## Comments

```bash
jira comments PROJ-123                        # List comments
jira comment PROJ-123 --text "Work completed"  # Add comment
```

## Time Tracking

```bash
jira worklogs PROJ-123                        # List worklogs
jira worklog PROJ-123 --timeSpent 2h          # Log 2 hours
jira worklog PROJ-123 --timeSpent 1d          # Log 1 day
jira worklog PROJ-123 12345                   # Get specific worklog
```

## Links

```bash
# Issue links
jira links PROJ-123                           # List issue links
jira linktypes                                # Available link types
jira link --inward PROJ-1 --outward PROJ-2 --type Blocks

# Web links
jira weblinks PROJ-123                        # List web/remote links
jira weblink PROJ-123 --url "https://..." --title "Link title"
```

## Attachments & Watchers

```bash
jira attachments PROJ-123                     # List attachments
jira watchers PROJ-123                        # List watchers
jira watcher PROJ-123 --username john         # Add watcher
```

## Project Data

```bash
jira projects                                 # List all projects
jira project PROJ                             # Project details
jira components PROJ                          # Project components
jira versions PROJ                            # Project versions
```

## Reference Data

```bash
jira priorities                               # Priority levels
jira statuses                                 # All statuses
jira status "In Progress"                     # Single status details
jira fields                                   # All fields
jira filters                                  # Your saved filters
jira filter 12345                             # Single filter
```

## User & Health

```bash
jira user me                                  # Current user
jira health                                   # Check connection
```

## Output Formats

All commands support `--format`:

```bash
jira issue PROJ-123 --format json     # Default. Raw JSON
jira issue PROJ-123 --format ai       # Token-efficient for LLMs
jira issue PROJ-123 --format rich     # Terminal colors
jira issue PROJ-123 --format markdown # Markdown tables
```

## Help

```bash
jira --help                                   # List all commands
jira help                                     # Same as above
jira help search                              # Search command help
jira issue --help                             # Issue command help
```
