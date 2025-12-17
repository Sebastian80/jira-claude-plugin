"""
Search tools - JQL search operations.

Tools:
- SearchIssues: Search issues using JQL
"""

import re
from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext

from ..response import formatted, formatted_error

__all__ = ["SearchIssues"]


def preprocess_jql(jql: str) -> str:
    """Pre-process JQL to fix common issues.

    Converts:
    - `field != value` → `NOT field = value`
    - `field \\!= value` → `NOT field = value` (escaped variant)
    - `field !~ value` → `NOT field ~ value`
    - `field \\!~ value` → `NOT field ~ value` (escaped variant)
    """
    jql = re.sub(
        r'(\w+)\s*\\?!=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|\S+)',
        r'NOT \1 = \2',
        jql
    )
    jql = re.sub(
        r'(\w+)\s*\\?!~\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|\S+)',
        r'NOT \1 ~ \2',
        jql
    )
    return jql


class SearchIssues(Tool):
    """Search issues using JQL query."""

    jql: str = Field(..., description="JQL query string")
    max_results: int = Field(50, alias="maxResults", ge=1, le=100, description="Maximum results (1-100)")
    start_at: int = Field(0, alias="startAt", ge=0, description="Index of first result (pagination)")
    fields: str = Field(
        "key,summary,status,assignee,priority,issuetype",
        description="Comma-separated fields to return"
    )
    format: str = Field("json", description="Output format: json, human, ai, markdown")

    class Meta:
        method = "GET"
        path = "/search"
        tags = ["search"]

    async def execute(self, ctx: ToolContext) -> Any:
        field_list = [f.strip() for f in self.fields.split(",")]
        processed_jql = preprocess_jql(self.jql)

        try:
            results = ctx.client.jql(
                processed_jql,
                limit=self.max_results,
                start=self.start_at,
                fields=field_list
            )
            issues = results.get("issues", [])

            if self.format == "json":
                return {
                    "success": True,
                    "data": issues,
                    "pagination": {
                        "startAt": self.start_at,
                        "maxResults": self.max_results,
                        "total": results.get("total", len(issues)),
                        "returned": len(issues),
                    },
                }
            return formatted(issues, self.format, "search")
        except Exception as e:
            error_msg = str(e)
            hint = "Check JQL syntax"
            if "field" in error_msg.lower():
                hint = "Invalid field name"
            elif "does not exist" in error_msg.lower():
                hint = "Value does not exist"
            return formatted_error(f"JQL error: {e}", hint=hint, fmt=self.format)
