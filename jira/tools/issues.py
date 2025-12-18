"""
Issue tools - CRUD operations for Jira issues.

Tools:
- GetIssue: Get issue details by key (with field validation and link expansion)
- GetIssues: Get multiple issues by keys (bulk fetch)
- CreateIssue: Create new issue
- UpdateIssue: Update issue fields
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetIssue", "GetIssues", "CreateIssue", "UpdateIssue"]

# Standard Jira fields for validation
KNOWN_FIELDS = {
    "summary", "description", "status", "priority", "assignee", "reporter",
    "created", "updated", "duedate", "resolution", "resolutiondate",
    "issuetype", "project", "labels", "components", "fixVersions",
    "affectsVersions", "issuelinks", "subtasks", "parent", "comment",
    "worklog", "attachment", "timetracking", "timeestimate", "timespent",
    "aggregatetimeestimate", "aggregatetimespent", "environment", "votes",
    "watches", "creator", "progress", "aggregateprogress",
}


def _validate_fields(requested: str, issue_data: dict) -> str | None:
    """Check if requested fields returned valid data, warn about potential issues.

    Args:
        requested: Comma-separated field names that were requested
        issue_data: The returned issue data

    Returns:
        Warning message if issues detected, None otherwise
    """
    if not requested:
        return None

    fields_obj = issue_data.get("fields", {})
    requested_list = [f.strip().lower() for f in requested.split(",")]

    # Check for unknown fields
    unknown = [f for f in requested_list if f not in KNOWN_FIELDS and not f.startswith("customfield_")]

    # Check for fields that came back as None (might be invalid or just empty)
    none_fields = [f for f in requested_list if fields_obj.get(f) is None]

    warnings = []
    if unknown:
        warnings.append(f"Unknown fields (may be custom): {', '.join(unknown)}")
    if len(none_fields) == len(requested_list) and len(requested_list) > 1:
        warnings.append(f"All requested fields returned None - check field names")

    return "; ".join(warnings) if warnings else None


def _extract_linked_issues(issue: dict) -> list[dict]:
    """Extract linked issue summaries from issue links.

    The Jira API already includes linked issue summaries in the issuelinks field,
    so we don't need to make additional requests.

    Args:
        issue: Issue data with issuelinks field

    Returns:
        List of linked issue info dicts with key, summary, status, type, direction
    """
    linked = []
    links = issue.get("fields", {}).get("issuelinks", [])
    for link in links:
        link_type = link.get("type", {}).get("name", "?")

        if "inwardIssue" in link:
            li = link["inwardIssue"]
            linked.append({
                "key": li.get("key"),
                "summary": li.get("fields", {}).get("summary"),
                "status": li.get("fields", {}).get("status", {}).get("name"),
                "type": li.get("fields", {}).get("issuetype", {}).get("name"),
                "link_type": f"{link.get('type', {}).get('inward', link_type)}",
            })
        if "outwardIssue" in link:
            li = link["outwardIssue"]
            linked.append({
                "key": li.get("key"),
                "summary": li.get("fields", {}).get("summary"),
                "status": li.get("fields", {}).get("status", {}).get("name"),
                "type": li.get("fields", {}).get("issuetype", {}).get("name"),
                "link_type": f"{link.get('type', {}).get('outward', link_type)}",
            })
    return linked


class GetIssue(Tool):
    """Get issue details by key.

    Features:
    - Field validation: warns about potentially invalid field names
    - Link expansion: --include-links fetches linked issue summaries
    """

    key: str = Field(..., description="Issue key like PROJ-123")
    fields: str | None = Field(None, description="Comma-separated fields to return")
    expand: str | None = Field(None, description="Fields to expand (e.g., 'changelog')")
    include_links: bool = Field(False, description="Include linked issue summaries")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/issue/{key}"
        tags = ["issues"]

    async def execute(self, ctx: ToolContext) -> Any:
        params = {}
        if self.fields:
            # Ensure issuelinks is included if include_links is requested
            fields_list = self.fields
            if self.include_links and "issuelinks" not in self.fields.lower():
                fields_list = f"{self.fields},issuelinks"
            params["fields"] = fields_list
        elif self.include_links:
            # Default fields plus issuelinks
            params["fields"] = "summary,status,priority,issuetype,assignee,issuelinks"
        if self.expand:
            params["expand"] = self.expand

        try:
            issue = ctx.client.issue(self.key, **params)

            # Validate fields if specific fields were requested
            warning = _validate_fields(self.fields, issue)

            # Extract linked issues if requested (already included in response, no extra requests)
            if self.include_links:
                linked_issues = _extract_linked_issues(issue)
                if linked_issues:
                    issue["_linked_issues"] = linked_issues

            # Add warning to response if present
            if warning:
                issue["_warning"] = warning

            return formatted(issue, self.format, "issue")
        except Exception as e:
            if "does not exist" in str(e).lower() or "404" in str(e):
                return ToolResult(error=f"Issue {self.key} not found", status=404)
            return ToolResult(error=str(e), status=500)


class GetIssues(Tool):
    """Get multiple issues by keys in a single request.

    More efficient than calling GetIssue multiple times.
    Uses JQL internally: key in (KEY1, KEY2, ...)

    Example:
        jira issues HMKG-1,HMKG-2,HMKG-3
        jira issues "HMKG-1 HMKG-2 HMKG-3"
    """

    keys: str = Field(..., description="Comma or space-separated issue keys")
    fields: str | None = Field(None, description="Comma-separated fields to return")
    format: str = Field("ai", description="Output format: json, rich, ai, markdown")

    class Meta:
        method = "GET"
        path = "/issues"
        tags = ["issues"]

    async def execute(self, ctx: ToolContext) -> Any:
        import asyncio

        # Parse keys - support comma, space, or mixed separators
        raw_keys = self.keys.replace(",", " ").split()
        keys_list = [k.strip() for k in raw_keys if k.strip()]

        if not keys_list:
            return ToolResult(error="No issue keys provided", status=400)

        if len(keys_list) > 50:
            return ToolResult(error="Maximum 50 issues per request", status=400)

        params = {}
        if self.fields:
            params["fields"] = self.fields

        def fetch_one(key: str) -> tuple[str, dict | None, str | None]:
            """Fetch single issue, return (key, issue_data, error_msg)."""
            try:
                issue = ctx.client.issue(key, **params)
                return (key, issue, None)
            except Exception as e:
                err_str = str(e).lower()
                if "does not exist" in err_str or "404" in err_str or "nicht" in err_str:
                    return (key, None, "not_found")
                return (key, None, str(e))

        try:
            # Parallel fetch using thread pool (client is sync)
            tasks = [asyncio.to_thread(fetch_one, key) for key in keys_list]
            results = await asyncio.gather(*tasks)

            issues = []
            missing = []
            errors = []

            for key, issue_data, error in results:
                if issue_data:
                    issues.append(issue_data)
                elif error == "not_found":
                    missing.append(key)
                else:
                    errors.append(f"{key}: {error}")

            # If all failed with real errors, report
            if errors and not issues:
                return ToolResult(error=f"Fetch failed: {'; '.join(errors)}", status=500)

            response = {
                "total": len(issues),
                "issues": issues,
            }
            if missing:
                response["missing"] = missing
                response["_warning"] = f"Issues not found: {', '.join(missing)}"

            return formatted(response, self.format, "search")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class CreateIssue(Tool):
    """Create new issue in Jira."""

    project: str = Field(..., description="Project key")
    summary: str = Field(..., description="Issue title/summary")
    issue_type: str = Field(..., alias="type", description="Issue type: Story, Bug, Task, etc.")
    description: str | None = Field(None, description="Issue description")
    priority: str | None = Field(None, description="Priority: Highest, High, Medium, Low, Lowest")
    labels: str | None = Field(None, description="Comma-separated labels")
    assignee: str | None = Field(None, description="Username or email of assignee")
    parent: str | None = Field(None, description="Parent issue key (for subtasks)")

    class Meta:
        method = "POST"
        path = "/create"
        tags = ["issues"]

    async def execute(self, ctx: ToolContext) -> Any:
        issue_fields = {
            "project": {"key": self.project},
            "summary": self.summary,
            "issuetype": {"name": self.issue_type},
        }

        if self.description:
            issue_fields["description"] = self.description
        if self.priority:
            issue_fields["priority"] = {"name": self.priority}
        if self.labels:
            issue_fields["labels"] = [label.strip() for label in self.labels.split(",")]
        if self.assignee:
            if "@" in self.assignee:
                issue_fields["assignee"] = {"emailAddress": self.assignee}
            else:
                issue_fields["assignee"] = {"name": self.assignee}
        if self.parent:
            issue_fields["parent"] = {"key": self.parent}

        try:
            result = ctx.client.create_issue(fields=issue_fields)
            return ToolResult(data=result, status=201)
        except Exception as e:
            return ToolResult(error=str(e), status=400)


class UpdateIssue(Tool):
    """Update issue fields."""

    key: str = Field(..., description="Issue key to update")
    summary: str | None = Field(None, description="New issue summary/title")
    priority: str | None = Field(None, description="Priority: Highest, High, Medium, Low, Lowest")
    labels: str | None = Field(None, description="Comma-separated labels (replaces existing)")
    assignee: str | None = Field(None, description="Username or email of assignee")

    class Meta:
        method = "PATCH"
        path = "/issue/{key}"
        tags = ["issues"]

    async def execute(self, ctx: ToolContext) -> Any:
        update_fields = {}

        if self.summary:
            update_fields["summary"] = self.summary
        if self.priority:
            update_fields["priority"] = {"name": self.priority}
        if self.labels:
            update_fields["labels"] = [label.strip() for label in self.labels.split(",")]
        if self.assignee:
            if "@" in self.assignee:
                update_fields["assignee"] = {"emailAddress": self.assignee}
            else:
                update_fields["assignee"] = {"name": self.assignee}

        if not update_fields:
            return ToolResult(error="No fields specified to update", status=400)

        try:
            ctx.client.update_issue_field(self.key, update_fields)
            return ToolResult(data={"key": self.key, "updated": list(update_fields.keys())})
        except Exception as e:
            return ToolResult(error=str(e), status=500)
