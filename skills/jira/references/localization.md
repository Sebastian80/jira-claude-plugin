# Localized Jira Instances

If your Jira displays German (or other language) status names, **JQL requires internal status names, not display names**.

## Common Status Mappings

| Display Name | JQL Value |
|--------------|-----------|
| Geschlossen | Closed |
| Offen | Open |
| In Arbeit | In Progress |
| Erledigt | Resolved |
| Zu erledigen | To Do |

## Finding the Correct Status Name

Use `jira statuses` to list all statuses and their IDs:
```bash
jira statuses --format json | grep -i "name"
```

Then use the exact `name` value in JQL, not the translated display name.

## Example Error

```
# This FAILS (display name)
jira search --jql 'status = "In Arbeit"'
# Error: Der Wert 'In Arbeit' existiert nicht für das Feld 'status'.

# This WORKS (internal name)
jira search --jql 'status = "In Progress"'
```
