# Jira CLI Command Reference

Full command reference. Use `jira --help` for latest.

## Issues

```bash
jira issue PROJ-123                    # Get issue details
jira issue PROJ-123 --fields summary,status  # Specific fields
jira issue PROJ-123 --expand changelog # Include change history
jira create --project PROJ --type Task --summary "New task"
```

## Search

```bash
jira search --jql "assignee = currentUser()"
jira search --jql "project = PROJ" --maxResults 50
```

## Transitions

```bash
jira transitions PROJ-123              # List available transitions
jira transition PROJ-123 --transition "In Progress"
```

## Comments

```bash
jira comments PROJ-123                 # List comments
jira comment PROJ-123 --body "Done"    # Add comment
```

## Time Tracking

```bash
jira worklogs PROJ-123                 # List worklogs
jira worklog PROJ-123 --timeSpent 2h   # Log time
jira worklog PROJ-123 12345            # Get specific worklog
```

## Links

```bash
jira links PROJ-123                    # Issue links
jira linktypes                         # Available link types
jira link --inward PROJ-1 --outward PROJ-2 --type Blocks
jira weblinks PROJ-123                 # Web/remote links
jira weblink PROJ-123 --url "https://..." --title "Link title"
```

## Attachments & Watchers

```bash
jira attachments PROJ-123              # List attachments
jira watchers PROJ-123                 # List watchers
jira watcher PROJ-123 --username john  # Add watcher
```

## Project Data

```bash
jira projects                          # List all projects
jira project PROJ                      # Project details
jira components PROJ                   # Project components
jira versions PROJ                     # Project versions
```

## Reference Data

```bash
jira priorities                        # Priority levels
jira statuses                          # All statuses
jira fields                            # All fields
jira filters                           # Your saved filters
jira user me                           # Current user
```

## Health

```bash
jira health                            # Check connection
```
