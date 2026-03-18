# Localized Jira Instances

## JQL Requires Internal Status Names

If your Jira displays German (or other localized) status names, **JQL requires the internal English status names, not the display names**.

### Common Status Mappings

| Display Name (German) | JQL Value (English) |
|------------------------|---------------------|
| Offen | Open |
| Geschlossen | Closed |
| In Arbeit | In Progress |
| Erledigt | Resolved |
| Zu erledigen | To Do |
| Fertig | Done |
| Neu | New |
| Wieder geöffnet | Reopened |

### Example

```bash
# FAILS — localized display name
jira search --jql 'status = "In Arbeit"'
# Error: Der Wert 'In Arbeit' existiert nicht für das Feld 'status'.

# WORKS — internal English name
jira search --jql 'status = "In Progress"'
```

## CLI Status Endpoint Accepts Both

The `jira status` command handles bidirectional lookup automatically:

```bash
jira status "In Progress"    # English name — works
jira status "In Arbeit"      # German name — also works
```

## Finding Status Names

Use `jira statuses` to list all statuses with their internal names:

```bash
jira statuses --format ai
```
