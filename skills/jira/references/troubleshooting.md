# Troubleshooting Guide

## Quick Health Check

```bash
# Check Jira connection
jira health

# Verify Jira credentials
jira user me

# Check server status
jira status
```

## Configuration

Credentials loaded from `~/.env.jira`:

### Jira Cloud
```bash
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
```

### Jira Server/Data Center
```bash
JIRA_URL=https://jira.yourcompany.com
JIRA_PERSONAL_TOKEN=your-personal-access-token
```

## Common Errors

### "Server not running"

**Cause**: Jira server not started or port 9200 in use.

**Fix**:
1. Check server status: `jira status`
2. Check if something else uses port 9200: `ss -tlnp | grep 9200`
3. View server logs: `jira logs`
4. Restart server: `jira restart`

### "Connection failed" / "Connection reset"

**Cause**: Network issue or server crashed.

**Fix**:
1. Check server status: `jira status`
2. View logs for errors: `jira logs`
3. Restart if needed: `jira restart`

### "401 Unauthorized"

**Cause**: Invalid credentials.

**Cloud Fix**:
1. Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens
2. Use email as `JIRA_USERNAME`, not display name

**Server/DC Fix**:
1. Create PAT in Jira: Profile → Personal Access Tokens
2. Use only `JIRA_PERSONAL_TOKEN`, not username/password

### "403 Forbidden"

**Cause**: Valid auth but no permission.

**Fix**:
1. Verify account has project access
2. Check if IP allowlisting blocks API access
3. Confirm API access not disabled by admin

### "Issue does not exist"

**Cause**: Wrong key or no permission.

**Fix**:
1. Verify issue key spelling and case
2. Confirm you have "Browse" permission on project
3. Check if issue was moved/deleted

### "detail: Not Found"

**Cause**: Wrong command syntax or endpoint doesn't exist.

**Fix**:
1. Check command with `jira help`
2. Positional args become path: `jira user me` → `/jira/user/me`

## Debug Mode

```bash
# Check Jira health
jira health

# Check server status
jira status

# View server logs
jira logs

# Test direct API call (GET)
curl -s "http://127.0.0.1:9200/jira/user/me"

# Direct API call (POST/PATCH) — must use JSON body, not query params
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"text": "Hello"}' "http://127.0.0.1:9200/jira/comment/PROJ-123"

# View OpenAPI docs
curl -s "http://127.0.0.1:9200/openapi.json" | jq '.paths | keys'
```

## JQL Issues

### "Value does not exist for field 'status'"

**Cause**: Using localized status names (e.g., German "Geschlossen") in JQL.

**Fix**: Always use **English status names** in JQL, regardless of your Jira's display language:

| Display (German) | JQL Value (English) |
|------------------|---------------------|
| Geschlossen | Closed |
| Offen | Open |
| In Arbeit | In Progress |
| Erledigt | Resolved |
| Zu erledigen | To Do |

```bash
# Wrong (German display name)
jira search --jql 'status = Geschlossen'

# Correct (English JQL value)
jira search --jql 'status = Closed'
```

### Bash history expansion with negation operators

**Cause**: Bash interprets the exclamation mark in double quotes as history expansion.

**Fix**: Use single quotes for JQL, or use alternative syntax:

```bash
# Option 1: Single quotes (recommended)
jira search --jql 'status not in (Done)'

# Option 2: NOT syntax
jira search --jql 'NOT status = Done'
```

The plugin auto-converts negation operators to `NOT ... =` as a fallback.

## Auth Mode Detection

The server auto-detects auth mode:
- If `JIRA_PERSONAL_TOKEN` set → Server/DC PAT auth
- If `JIRA_USERNAME` + `JIRA_API_TOKEN` set → Cloud basic auth
- URL containing `.atlassian.net` → Cloud mode

## Server Management

```bash
jira start      # Start server (auto-starts on first command)
jira stop       # Stop server
jira status     # Show server status
jira restart    # Restart server (pick up code changes)
jira logs       # Tail server logs
```
