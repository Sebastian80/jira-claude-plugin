# Jira CLI Command Reference

Full command reference. Use `jira help` for latest.

## Issues

```bash
# Get issue
jira issue PROJ-123                           # Get issue details (JSON)
jira issue PROJ-123 --format ai               # Token-efficient for LLMs
jira issue PROJ-123 --fields summary,status    # Specific fields only
jira issue PROJ-123 --expand changelog         # Include change history

# Combined view (issue + comments in one call)
jira show PROJ-123                            # Issue details with comments
jira show PROJ-123 --format ai                # Token-efficient combined view

# Bulk fetch — use search instead
jira search --jql 'key in (PROJ-1, PROJ-2, PROJ-3)'

# Create issue
jira create --project PROJ --type Task --summary "New task"
jira create --project PROJ --type Bug --summary "Fix login" \
  --assignee john --priority High \
  --description "Login fails on mobile"
jira create --project PROJ --type Story --summary "Story" \
  --parent PROJ-100                           # Sub-task of PROJ-100
jira create --project PROJ --type Task --summary "Task" \
  --labels "backend,api"                      # Comma-separated labels
jira create --project PROJ --type Task --summary "Custom" \
  --custom '{"customfield_10001": "value"}'   # Arbitrary fields via JSON

# Update issue (PATCH)
jira update PROJ-123 --summary "Updated title"
jira update PROJ-123 --assignee jane --priority Low
jira update PROJ-123 --description "New description"
jira update PROJ-123 --labels "backend,frontend"
jira update PROJ-123 --custom '{"customfield_10001": "new value"}'

# Delete issue
jira delete PROJ-123
```

**Create parameters:** `--project`\*, `--type`\*, `--summary`\* (required), `--description`, `--priority`, `--labels`, `--assignee`, `--parent`, `--custom`

**Update parameters:** `--summary`, `--description`, `--priority`, `--labels`, `--assignee`, `--custom` (at least one required)

## Search

```bash
jira search --jql 'assignee = currentUser()'
jira search --jql 'project = PROJ' --maxResults 50
jira search --jql 'status not in (Done, Closed)'
jira search --jql 'updated >= -7d' --startAt 50      # Pagination
jira search --jql 'project = PROJ' --fields key,summary,status
```

**Note:** Use single quotes for JQL to avoid bash history expansion.

## Transitions

```bash
jira transitions PROJ-123                     # List available transitions
jira transition PROJ-123 --target "In Progress"
jira transition PROJ-123 --target "Done" --comment true  # Add transition trail
jira transition PROJ-123 --target "Done" --dryRun true   # Preview without executing
jira transition PROJ-123 --target "Done" --maxSteps 3    # Limit intermediate steps
```

## Comments

```bash
jira comments PROJ-123                        # List comments (newest first)
jira comments PROJ-123 --limit 5              # Limit number of comments
jira comment PROJ-123 --text "Work completed" # Add comment
jira comment PROJ-123 12345 -X DELETE         # Delete comment by ID
```

## Time Tracking

```bash
jira worklogs PROJ-123                        # List worklogs
jira worklog PROJ-123 --timeSpent 2h          # Log 2 hours (required)
jira worklog PROJ-123 --timeSpent 1d --comment "Sprint work"
jira worklog PROJ-123 --timeSpent 30m --started "2026-03-18T09:00:00.000+0100"
jira worklog PROJ-123 12345                   # Get specific worklog by ID
```

**Note:** `--timeSpent` is required. Formats: `30m`, `2h`, `1d`, `1d 4h`.

## Links

```bash
# Issue links
jira links PROJ-123                           # List issue links
jira linktypes                                # Available link types
jira link --from PROJ-1 --to PROJ-2 --type "Relation"

# Web links
jira weblinks PROJ-123                        # List web/remote links
jira weblink PROJ-123 --url "https://..." --title "Link title"
jira weblink PROJ-123 12345 -X DELETE         # Remove web link by ID
```

**Link type names** (use the name, NOT the description):
`Relation`, `Blockade`, `Cause`, `Duplicate`, `Resolve`, `Mention`, etc.
Use `jira linktypes` to see all available types on your instance.

## Sprints

```bash
# Boards
jira boards                                   # List all boards
jira boards --project PROJ                    # Boards for a project
jira boards --type scrum                      # Filter by type

# Sprints
jira sprint active PROJ                       # Get active sprint for project
jira sprint 915                               # Get sprint details by ID
jira sprints 119                              # List sprints for board 119
jira sprints 119 --state active               # Filter: active, future, closed

# Add/remove issues (requires positional 'issues' path segment)
jira sprint 915 issues --issues PROJ-123 -X POST      # Add issue to sprint
jira sprint 915 issues --issues PROJ-123 -X DELETE     # Remove from sprint
jira sprint 915 issues --issues "PROJ-1,PROJ-2" -X POST  # Multiple issues
```

## Attachments

```bash
jira attachments PROJ-123                     # List attachments
jira attachment PROJ-123 --file report.pdf    # Upload single file
jira attachment PROJ-123 --file a.pdf --file b.png  # Upload multiple files
jira attachment 12345 -X DELETE               # Delete attachment by ID
```

## Watchers

```bash
jira watchers PROJ-123                        # List watchers
jira watcher PROJ-123 --username john         # Add watcher
jira watcher PROJ-123 john -X DELETE          # Remove watcher
```

## Project Data

```bash
jira projects                                 # List all projects
jira projects --includeArchived true          # Include archived
jira project PROJ                             # Project details
jira components PROJ                          # Project components
jira versions PROJ                            # Project versions
```

## Versions

```bash
jira versions PROJ                            # List versions in project
jira version --project PROJ --name "v2.0"     # Create version
jira version 12345                            # Get version by ID
jira version 12345 -X PATCH --name "v2.1"    # Update version
```

## Components

```bash
jira components PROJ                          # List components in project
jira component --project PROJ --name "API"    # Create component
jira component 12345                          # Get component by ID
jira component 12345 -X DELETE               # Delete component
```

## Reference Data

```bash
jira priorities                               # Priority levels
jira statuses                                 # All statuses
jira status "In Progress"                     # Single status details
jira fields                                   # All fields
jira fields custom                            # Only custom fields
jira filters                                  # Your saved filters
jira filter 12345                             # Single filter details
```

## User & Health

```bash
jira user                                     # Current user info
jira user me                                  # Same as above (alias)
jira health                                   # Check Jira connection
```

## Output Formats

All commands support `--format`:

```bash
jira issue PROJ-123 --format json     # Default. Raw JSON wrapped in {success, data}
jira issue PROJ-123 --format ai       # Token-efficient for LLMs
jira issue PROJ-123 --format rich     # Terminal colors and panels
jira issue PROJ-123 --format markdown # Markdown tables
```

## Server Management

```bash
jira start      # Start server (auto-starts on first command)
jira stop       # Stop server
jira status     # Show server status
jira restart    # Restart server
jira logs       # Tail server logs
```

## Help

```bash
jira help                  # Full command list
jira help search           # Search endpoint help
jira help transition       # Transition endpoint help
```
