"""
Workflow tools - Transitions and workflow operations.

Tools:
- GetTransitions: Get available transitions for an issue
- Transition: Transition issue to new status
- GetWorkflows: Get project workflows
"""

from typing import Any

from pydantic import Field

from toolbus.tools import Tool, ToolContext, ToolResult

from ..response import formatted

__all__ = ["GetTransitions", "Transition", "GetWorkflows"]


class GetTransitions(Tool):
    """Get available transitions for an issue."""

    key: str = Field(..., description="Issue key")
    format: str = Field("ai", description="Output format: json, rich, ai")

    class Meta:
        method = "GET"
        path = "/transitions/{key}"
        tags = ["workflow"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            transitions = ctx.client.get_issue_transitions(self.key)
            return formatted(transitions, self.format, "transitions")
        except Exception as e:
            return ToolResult(error=str(e), status=500)


class Transition(Tool):
    """Transition issue to new status."""

    key: str = Field(..., description="Issue key")
    transition: str = Field(..., description="Transition name or ID")
    comment: str | None = Field(None, description="Optional comment for transition")
    resolution: str | None = Field(None, description="Resolution (for Done transitions)")

    class Meta:
        method = "POST"
        path = "/transition/{key}"
        tags = ["workflow"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            # Find transition ID by name or validate ID exists
            transitions = ctx.client.get_issue_transitions(self.key)
            transition_id = None
            transition_name = None

            for t in transitions:
                if str(t["id"]) == self.transition or t["name"].lower() == self.transition.lower():
                    transition_id = t["id"]
                    transition_name = t["name"]
                    break

            if not transition_id:
                available = [t["name"] for t in transitions]
                return ToolResult(
                    error=f"Transition '{self.transition}' not found. Available: {available}",
                    status=400
                )

            ctx.client.set_issue_status_by_transition_id(self.key, transition_id)
            return ToolResult(data={"key": self.key, "transition": transition_name})
        except Exception as e:
            return ToolResult(error=str(e), status=400)


class GetWorkflows(Tool):
    """Get workflows for a project."""

    project: str = Field(..., description="Project key")

    class Meta:
        method = "GET"
        path = "/workflows/{project}"
        tags = ["workflow"]

    async def execute(self, ctx: ToolContext) -> Any:
        try:
            # Get all workflows (no project-specific API available)
            workflows = ctx.client.get_all_workflows()
            return ToolResult(data=workflows)
        except Exception as e:
            return ToolResult(error=str(e), status=500)
