---
name: jira-bulk
description: Bulk Jira operations - mass transitions, updates, or modifications across multiple tickets. Use when changing state or fields on more than one ticket.
context: fork
agent: jira-agent
disable-model-invocation: true
---

Execute bulk Jira operations as requested.

$ARGUMENTS

**Mandatory protocol:**
1. Search and identify all affected tickets
2. Show a preview table (ticket key, current state, intended change) and get confirmation
3. Use `--dryRun` to validate transitions before executing
4. Execute changes, logging any failures
5. Report results: successes, failures, and any tickets that need manual attention
