# Troubleshooting Guide

## Quick Health Check

```bash
jira health     # Check Jira connection
jira user       # Verify credentials
jira status     # Check server status
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

Auth mode is auto-detected:
- If `JIRA_PERSONAL_TOKEN` is set → Server/DC PAT auth
- If `JIRA_USERNAME` + `JIRA_API_TOKEN` are set → Cloud basic auth
- URL containing `.atlassian.net` → Cloud mode (auto-detected if `JIRA_CLOUD` not set)

## Common Errors

### "Server not running"

**Cause**: Server not started or port 9200 in use.

**Fix**:
1. Check server status: `jira status`
2. Check if something else uses port 9200: `ss -tlnp | grep 9200`
3. View server logs: `jira logs`
4. Restart server: `jira restart`

### "Connection failed" / "Connection reset"

**Cause**: Network issue or server crashed.

**Fix**:
1. View logs for errors: `jira logs`
2. Restart: `jira restart`

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
1. Check command syntax with `jira help`
2. Positional args become URL path segments: `jira user me` → `/jira/user/me`
3. Missing required path parameter: `jira issue` needs a key → `jira issue PROJ-123`

### Flags silently ignored

**Cause**: Using flags that don't exist on an endpoint. GET endpoints ignore unknown query params.

**Fix**: Use dedicated commands instead of flags on `jira issue`:
- Links: `jira link`, not `jira issue KEY --link ...`
- Sprint: `jira sprint`, not `jira issue KEY --sprint ...`
- Use `jira help <command>` to see valid parameters

## JQL Issues

### "Value does not exist for field 'status'"

**Cause**: Using localized status names (e.g., German "Geschlossen") in JQL.

**Fix**: Use English status names in JQL. See [localization.md](localization.md) for mappings.

```bash
# Wrong (German display name)
jira search --jql 'status = Geschlossen'

# Correct (English JQL value)
jira search --jql 'status = Closed'
```

### Bash history expansion with negation operators

**Cause**: Bash interprets `!` in double quotes as history expansion.

**Fix**: Use single quotes for JQL, or use `NOT` syntax:

```bash
# Option 1: Single quotes (recommended)
jira search --jql 'status not in (Done)'

# Option 2: NOT syntax
jira search --jql 'NOT status = Done'
```

The CLI auto-converts `!=` and `!~` to `NOT ... =` and `NOT ... ~` as a fallback.

## Server Management

```bash
jira start      # Start server (auto-starts on first command)
jira stop       # Stop server
jira status     # Show server status + health info
jira restart    # Stop + start (picks up code/config changes)
jira logs       # Tail server logs
```

Server PID and logs are stored in `~/.local/share/jira-cli/`.
