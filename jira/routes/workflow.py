"""
Workflow and transition operations.

Endpoints:
- GET /transitions/{key} - List available transitions
- POST /transition/{key} - Execute transition (smart multi-step, runtime path-finding)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..deps import jira
from ..lib.workflow import WorkflowError
from ..response import success, error, formatted, jira_error_handler, OutputFormat, FORMAT_QUERY

router = APIRouter()


class TransitionBody(BaseModel):
    target: str
    comment: bool = False
    dryRun: bool = False
    maxSteps: int = 5


@router.get("/transitions/{key}")
@jira_error_handler(not_found="Issue {key} not found")
def list_transitions(
    key: str,
    format: OutputFormat = FORMAT_QUERY,
    client=Depends(jira),
):
    """List available transitions for an issue."""
    transitions = client.get_issue_transitions(key)
    return formatted(transitions, format, "transitions")


@router.post("/transition/{key}")
def do_transition(key: str, body: TransitionBody, client=Depends(jira)):
    """Transition issue to target state (smart multi-step)."""
    try:
        from ..lib.workflow import smart_transition

        executed = smart_transition(
            client=client,
            issue_key=key,
            target_state=body.target,
            add_comment=body.comment,
            dry_run=body.dryRun,
            max_steps=body.maxSteps,
        )

        # Final state is the last transition's target, or target if no-op
        final_state = executed[-1].to if executed else body.target

        return success({
            "key": key,
            "dry_run": body.dryRun,
            "transitions": [{"id": t.id, "name": t.name, "to": t.to} for t in executed],
            "steps": len(executed),
            "final_state": final_state,
        })
    except WorkflowError as e:
        return error(str(e), hint="Use 'jira transitions ISSUE' to see available states")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
