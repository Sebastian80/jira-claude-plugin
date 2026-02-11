"""
Unit tests for jira/lib/workflow.py.

Tests the workflow graph, store, path-finding, and smart transition logic.
Uses mock Jira clients at the function boundary — no HTTP calls.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

from jira.lib.workflow import (
    Transition,
    WorkflowGraph,
    WorkflowStore,
    WorkflowError,
    PathNotFoundError,
    WorkflowNotFoundError,
    DiscoveryError,
    TransitionFailedError,
    discover_workflow,
    smart_transition,
)


# =============================================================================
# Exception Hierarchy
# =============================================================================


class TestExceptions:
    """Test custom exception classes carry expected attributes and messages."""

    def test_path_not_found_error(self):
        err = PathNotFoundError("Open", "Done", {"Open", "In Progress"})
        assert err.from_state == "Open"
        assert err.to_state == "Done"
        assert err.reachable == {"Open", "In Progress"}
        assert "No path from 'Open' to 'Done'" in str(err)
        assert isinstance(err, WorkflowError)

    def test_workflow_not_found_error(self):
        err = WorkflowNotFoundError("Epic")
        assert err.issue_type == "Epic"
        assert "Epic" in str(err)
        assert isinstance(err, WorkflowError)

    def test_discovery_error(self):
        err = DiscoveryError("TEST-1", "In Progress", {"Open", "In Progress"})
        assert err.issue_key == "TEST-1"
        assert err.stuck_at == "In Progress"
        assert err.discovered_states == {"Open", "In Progress"}
        assert "TEST-1" in str(err)
        assert isinstance(err, WorkflowError)

    def test_transition_failed_error(self):
        t = Transition(id="11", name="Close", to="Done")
        err = TransitionFailedError("TEST-1", t, "Open", "Permission denied")
        assert err.issue_key == "TEST-1"
        assert err.transition == t
        assert err.current_state == "Open"
        assert err.reason == "Permission denied"
        assert "Close" in str(err)
        assert isinstance(err, WorkflowError)


# =============================================================================
# Transition Dataclass
# =============================================================================


class TestTransition:
    """Test Transition dataclass serialization."""

    def test_to_dict(self):
        t = Transition(id="11", name="Start", to="In Progress")
        assert t.to_dict() == {"id": "11", "name": "Start", "to": "In Progress"}

    def test_from_dict(self):
        t = Transition.from_dict({"id": "21", "name": "Close", "to": "Done"})
        assert t.id == "21"
        assert t.name == "Close"
        assert t.to == "Done"

    def test_roundtrip(self):
        original = Transition(id="31", name="Reopen", to="Open")
        restored = Transition.from_dict(original.to_dict())
        assert restored == original


# =============================================================================
# WorkflowGraph
# =============================================================================


def _make_simple_graph():
    """Create a simple 3-state workflow: Open -> In Progress -> Done."""
    graph = WorkflowGraph(issue_type="Task", issue_type_id="10001")
    graph.add_state("Open", [
        Transition(id="11", name="Start Progress", to="In Progress"),
    ])
    graph.add_state("In Progress", [
        Transition(id="21", name="Close", to="Done"),
        Transition(id="31", name="Stop Progress", to="Open"),
    ])
    graph.add_state("Done", [
        Transition(id="41", name="Reopen", to="Open"),
    ])
    return graph


class TestWorkflowGraph:
    """Test WorkflowGraph data structure and BFS path-finding."""

    def test_transitions_from_existing_state(self):
        graph = _make_simple_graph()
        transitions = graph.transitions_from("Open")
        assert len(transitions) == 1
        assert transitions[0].to == "In Progress"

    def test_transitions_from_nonexistent_state(self):
        graph = _make_simple_graph()
        assert graph.transitions_from("Unknown") == []

    def test_all_states(self):
        graph = _make_simple_graph()
        states = graph.all_states()
        assert states == {"Open", "In Progress", "Done"}

    def test_add_state(self):
        graph = WorkflowGraph(issue_type="Task", issue_type_id="1")
        graph.add_state("New", [Transition(id="1", name="Start", to="Active")])
        assert len(graph.states) == 1
        assert "New" in graph.states

    def test_add_state_overwrites(self):
        graph = WorkflowGraph(issue_type="Task", issue_type_id="1")
        graph.add_state("Open", [Transition(id="1", name="Start", to="Active")])
        graph.add_state("Open", [Transition(id="2", name="Close", to="Done")])
        assert len(graph.states["Open"]) == 1
        assert graph.states["Open"][0].to == "Done"

    # --- BFS Path Finding ---

    def test_path_already_at_target(self):
        graph = _make_simple_graph()
        path = graph.path_to("Open", "Open")
        assert path == []

    def test_path_single_step(self):
        graph = _make_simple_graph()
        path = graph.path_to("Open", "In Progress")
        assert len(path) == 1
        assert path[0].to == "In Progress"

    def test_path_multi_step(self):
        graph = _make_simple_graph()
        path = graph.path_to("Open", "Done")
        assert len(path) == 2
        assert path[0].to == "In Progress"
        assert path[1].to == "Done"

    def test_path_reverse(self):
        graph = _make_simple_graph()
        path = graph.path_to("Done", "Open")
        assert len(path) == 1
        assert path[0].to == "Open"

    def test_path_case_insensitive(self):
        graph = _make_simple_graph()
        path = graph.path_to("Open", "in progress")
        assert len(path) == 1
        assert path[0].to == "In Progress"

    def test_path_case_insensitive_from_state(self):
        """from_state uses case-insensitive comparison for already-at-target check."""
        graph = _make_simple_graph()
        path = graph.path_to("open", "Open")
        assert path == []

    def test_path_partial_match_on_transition_name(self):
        """Target can partially match transition name."""
        graph = _make_simple_graph()
        path = graph.path_to("Open", "start")
        assert len(path) == 1
        assert path[0].name == "Start Progress"

    def test_path_not_found_raises(self):
        graph = WorkflowGraph(issue_type="Task", issue_type_id="1")
        graph.add_state("Open", [Transition(id="1", name="Start", to="Active")])
        graph.add_state("Active", [])
        # No path from Active to Closed
        with pytest.raises(PathNotFoundError) as exc_info:
            graph.path_to("Active", "Closed")
        assert exc_info.value.from_state == "Active"
        assert exc_info.value.to_state == "Closed"

    def test_path_shortest(self):
        """BFS finds shortest path even when longer paths exist."""
        graph = WorkflowGraph(issue_type="Task", issue_type_id="1")
        graph.add_state("A", [
            Transition(id="1", name="Via B", to="B"),
            Transition(id="2", name="Direct to C", to="C"),
        ])
        graph.add_state("B", [
            Transition(id="3", name="B to C", to="C"),
        ])
        path = graph.path_to("A", "C")
        assert len(path) == 1
        assert path[0].to == "C"

    # --- Reachability ---

    def test_reachable_from(self):
        graph = _make_simple_graph()
        reachable = graph.reachable_from("Open")
        assert reachable == {"Open", "In Progress", "Done"}

    def test_reachable_from_dead_end(self):
        graph = WorkflowGraph(issue_type="Task", issue_type_id="1")
        graph.add_state("A", [Transition(id="1", name="Go", to="B")])
        graph.add_state("B", [])
        reachable = graph.reachable_from("A")
        assert reachable == {"A", "B"}

    # --- Display ---

    def test_to_ascii(self):
        graph = _make_simple_graph()
        ascii_out = graph.to_ascii()
        assert "Workflow: Task" in ascii_out
        assert "[Open]" in ascii_out
        assert "Start Progress" in ascii_out

    def test_to_table(self):
        graph = _make_simple_graph()
        table = graph.to_table()
        assert "State" in table
        assert "Open" in table
        assert "In Progress" in table

    # --- Serialization ---

    def test_to_dict(self):
        graph = _make_simple_graph()
        graph.discovered_from = "TEST-1"
        graph.discovered_at = datetime(2024, 1, 15, 10, 0, 0)
        d = graph.to_dict()
        assert d["id"] == "10001"
        assert d["discovered_from"] == "TEST-1"
        assert d["discovered_at"] == "2024-01-15T10:00:00"
        assert "Open" in d["states"]
        assert len(d["states"]["Open"]) == 1

    def test_from_dict(self):
        data = {
            "id": "10001",
            "discovered_from": "TEST-1",
            "discovered_at": "2024-01-15T10:00:00",
            "states": {
                "Open": [{"id": "11", "name": "Start", "to": "Active"}],
            },
        }
        graph = WorkflowGraph.from_dict("Task", data)
        assert graph.issue_type == "Task"
        assert graph.issue_type_id == "10001"
        assert graph.discovered_from == "TEST-1"
        assert graph.discovered_at == datetime(2024, 1, 15, 10, 0, 0)
        assert len(graph.states["Open"]) == 1

    def test_from_dict_no_discovered_at(self):
        data = {"id": "1", "states": {}}
        graph = WorkflowGraph.from_dict("Bug", data)
        assert graph.discovered_at is None

    def test_roundtrip(self):
        original = _make_simple_graph()
        original.discovered_from = "TEST-1"
        original.discovered_at = datetime(2024, 1, 15, 10, 0, 0)
        restored = WorkflowGraph.from_dict("Task", original.to_dict())
        assert restored.issue_type == original.issue_type
        assert len(restored.states) == len(original.states)
        for state in original.states:
            assert len(restored.states[state]) == len(original.states[state])


# =============================================================================
# WorkflowStore
# =============================================================================


class TestWorkflowStore:
    """Test WorkflowStore persistence."""

    def test_init_creates_empty_store(self, tmp_path):
        store_file = tmp_path / "workflows.json"
        store = WorkflowStore(path=store_file)
        assert store.list_types() == []

    def test_save_and_get(self, tmp_path):
        store_file = tmp_path / "workflows.json"
        store = WorkflowStore(path=store_file)

        graph = _make_simple_graph()
        store.save(graph)

        loaded = store.get("Task")
        assert loaded is not None
        assert loaded.issue_type == "Task"
        assert len(loaded.states) == 3

    def test_get_nonexistent(self, tmp_path):
        store_file = tmp_path / "workflows.json"
        store = WorkflowStore(path=store_file)
        assert store.get("Nonexistent") is None

    def test_save_creates_file(self, tmp_path):
        store_file = tmp_path / "subdir" / "workflows.json"
        store = WorkflowStore(path=store_file)
        store.save(_make_simple_graph())
        assert store_file.exists()

    def test_save_writes_valid_json(self, tmp_path):
        store_file = tmp_path / "workflows.json"
        store = WorkflowStore(path=store_file)
        store.save(_make_simple_graph())

        data = json.loads(store_file.read_text())
        assert "_meta" in data
        assert "issue_types" in data
        assert "Task" in data["issue_types"]

    def test_save_updates_meta_timestamp(self, tmp_path):
        store_file = tmp_path / "workflows.json"
        store = WorkflowStore(path=store_file)
        store.save(_make_simple_graph())

        data = json.loads(store_file.read_text())
        assert data["_meta"]["updated_at"] is not None

    def test_list_types(self, tmp_path):
        store_file = tmp_path / "workflows.json"
        store = WorkflowStore(path=store_file)

        graph1 = _make_simple_graph()
        graph2 = WorkflowGraph(issue_type="Bug", issue_type_id="10002")
        store.save(graph1)
        store.save(graph2)

        types = store.list_types()
        assert "Task" in types
        assert "Bug" in types

    def test_delete_existing(self, tmp_path):
        store_file = tmp_path / "workflows.json"
        store = WorkflowStore(path=store_file)
        store.save(_make_simple_graph())

        assert store.delete("Task") is True
        assert store.get("Task") is None

    def test_delete_nonexistent(self, tmp_path):
        store_file = tmp_path / "workflows.json"
        store = WorkflowStore(path=store_file)
        assert store.delete("Nonexistent") is False

    def test_atomic_write(self, tmp_path):
        """Save writes to .tmp first then renames (atomic on POSIX)."""
        store_file = tmp_path / "workflows.json"
        store = WorkflowStore(path=store_file)
        store.save(_make_simple_graph())

        # The .tmp file should not remain after save
        tmp_file = store_file.with_suffix(".tmp")
        assert not tmp_file.exists()
        assert store_file.exists()

    def test_load_existing_file(self, tmp_path):
        store_file = tmp_path / "workflows.json"
        # Write a store file manually
        data = {
            "_meta": {"version": 1, "updated_at": None},
            "issue_types": {
                "Epic": {
                    "id": "10003",
                    "discovered_from": None,
                    "discovered_at": None,
                    "states": {
                        "Open": [{"id": "1", "name": "Start", "to": "Active"}],
                    },
                }
            },
        }
        store_file.write_text(json.dumps(data))

        store = WorkflowStore(path=store_file)
        assert "Epic" in store.list_types()
        graph = store.get("Epic")
        assert graph is not None
        assert len(graph.states["Open"]) == 1


# =============================================================================
# smart_transition
# =============================================================================


def _make_workflow_client(states_and_transitions: dict, initial_state: str = "Open"):
    """Create a mock client that simulates workflow behavior.

    Args:
        states_and_transitions: Maps state name to list of transition dicts
            e.g. {"Open": [{"id": "11", "name": "Start", "to": "In Progress"}]}
        initial_state: Starting state of the issue
    """
    client = MagicMock()
    current_state = {"value": initial_state}

    def issue_side_effect(key, **kwargs):
        fields = kwargs.get("fields", "")
        if fields == "status":
            return {"key": key, "fields": {"status": {"name": current_state["value"]}}}
        return {
            "key": key,
            "fields": {
                "status": {"name": current_state["value"]},
                "issuetype": {"name": "Task", "id": "10001"},
            },
        }

    def get_transitions_side_effect(key):
        state = current_state["value"]
        raw = states_and_transitions.get(state, [])
        return [
            {"id": t["id"], "name": t["name"], "to": {"name": t["to"]}}
            for t in raw
        ]

    def set_status_side_effect(key, status_name):
        current_state["value"] = status_name

    client.issue.side_effect = issue_side_effect
    client.get_issue_transitions.side_effect = get_transitions_side_effect
    client.set_issue_status.side_effect = set_status_side_effect
    client.issue_add_comment.return_value = None

    return client


class TestSmartTransition:
    """Test smart_transition runtime path-finding."""

    def test_already_at_target(self):
        client = _make_workflow_client({"Open": []}, initial_state="Open")
        result = smart_transition(client, "TEST-1", "Open")
        assert result == []
        # Should not call set_issue_status
        client.set_issue_status.assert_not_called()

    def test_already_at_target_case_insensitive(self):
        client = _make_workflow_client({"Open": []}, initial_state="Open")
        result = smart_transition(client, "TEST-1", "open")
        assert result == []

    def test_direct_transition(self):
        client = _make_workflow_client({
            "Open": [{"id": "11", "name": "Close", "to": "Done"}],
        })
        result = smart_transition(client, "TEST-1", "Done")
        assert len(result) == 1
        assert result[0].to == "Done"
        client.set_issue_status.assert_called_once_with("TEST-1", "Done")

    def test_multi_step_transition(self):
        client = _make_workflow_client({
            "Open": [{"id": "11", "name": "Start", "to": "In Progress"}],
            "In Progress": [{"id": "21", "name": "Close", "to": "Done"}],
        })
        result = smart_transition(client, "TEST-1", "Done")
        assert len(result) == 2
        assert result[0].to == "In Progress"
        assert result[1].to == "Done"

    def test_no_transitions_available(self):
        client = _make_workflow_client({"Open": []})
        with pytest.raises(PathNotFoundError):
            smart_transition(client, "TEST-1", "Done")

    def test_no_path_all_visited(self):
        """When all transitions lead back to visited states, raises PathNotFoundError."""
        client = _make_workflow_client({
            "Open": [{"id": "11", "name": "Start", "to": "Active"}],
            "Active": [{"id": "21", "name": "Back", "to": "Open"}],
        })
        with pytest.raises(PathNotFoundError):
            smart_transition(client, "TEST-1", "Done")

    def test_dry_run_does_not_execute(self):
        client = _make_workflow_client({
            "Open": [{"id": "11", "name": "Close", "to": "Done"}],
        })
        result = smart_transition(client, "TEST-1", "Done", dry_run=True)
        assert len(result) == 1
        assert result[0].to == "Done"
        client.set_issue_status.assert_not_called()

    def test_max_steps_exceeded(self):
        """When path requires more steps than max_steps, raises WorkflowError."""
        client = _make_workflow_client({
            "S1": [{"id": "1", "name": "Go", "to": "S2"}],
            "S2": [{"id": "2", "name": "Go", "to": "S3"}],
            "S3": [{"id": "3", "name": "Go", "to": "S4"}],
            "S4": [{"id": "4", "name": "Go", "to": "S5"}],
            "S5": [{"id": "5", "name": "Go", "to": "S6"}],
            "S6": [{"id": "6", "name": "Go", "to": "Target"}],
        }, initial_state="S1")
        with pytest.raises(WorkflowError, match="within 5 steps"):
            smart_transition(client, "TEST-1", "Target", max_steps=5)

    def test_custom_max_steps(self):
        """max_steps can be increased to allow longer paths."""
        client = _make_workflow_client({
            "S1": [{"id": "1", "name": "Go", "to": "S2"}],
            "S2": [{"id": "2", "name": "Go", "to": "S3"}],
            "S3": [{"id": "3", "name": "Go", "to": "Target"}],
        }, initial_state="S1")
        result = smart_transition(client, "TEST-1", "Target", max_steps=10)
        assert len(result) == 3
        assert result[-1].to == "Target"

    def test_transition_failure_raises(self):
        client = _make_workflow_client({
            "Open": [{"id": "11", "name": "Close", "to": "Done"}],
        })
        client.set_issue_status.side_effect = Exception("Permission denied")
        with pytest.raises(TransitionFailedError) as exc_info:
            smart_transition(client, "TEST-1", "Done")
        assert exc_info.value.reason == "Permission denied"
        assert exc_info.value.current_state == "Open"

    def test_add_comment_on_success(self):
        client = _make_workflow_client({
            "Open": [{"id": "11", "name": "Close", "to": "Done"}],
        })
        smart_transition(client, "TEST-1", "Done", add_comment=True)
        client.issue_add_comment.assert_called_once()
        comment = client.issue_add_comment.call_args[0][1]
        assert "Open" in comment
        assert "Done" in comment

    def test_add_comment_failure_does_not_raise(self):
        """Comment failure should not raise, but should log a warning."""
        client = _make_workflow_client({
            "Open": [{"id": "11", "name": "Close", "to": "Done"}],
        })
        client.issue_add_comment.side_effect = Exception("Comment failed")
        # Should not raise despite comment failure
        result = smart_transition(client, "TEST-1", "Done", add_comment=True)
        assert len(result) == 1

    def test_add_comment_failure_logs_warning(self, caplog):
        """Bug 4.2: Comment failure should log a warning, not be silently swallowed."""
        import logging
        client = _make_workflow_client({
            "Open": [{"id": "11", "name": "Close", "to": "Done"}],
        })
        client.issue_add_comment.side_effect = Exception("Comment failed")
        with caplog.at_level(logging.WARNING, logger="jira.lib.workflow"):
            smart_transition(client, "TEST-1", "Done", add_comment=True)
        assert any("Comment failed" in record.message for record in caplog.records)

    def test_no_comment_on_dry_run(self):
        client = _make_workflow_client({
            "Open": [{"id": "11", "name": "Close", "to": "Done"}],
        })
        smart_transition(client, "TEST-1", "Done", add_comment=True, dry_run=True)
        client.issue_add_comment.assert_not_called()

    def test_no_comment_when_already_at_target(self):
        client = _make_workflow_client({"Open": []}, initial_state="Open")
        smart_transition(client, "TEST-1", "Open", add_comment=True)
        client.issue_add_comment.assert_not_called()


# =============================================================================
# discover_workflow
# =============================================================================


class TestDiscoverWorkflow:
    """Test discover_workflow builds correct graph from API."""

    def test_single_state_discovery(self):
        """Discovers a simple workflow with transitions from the starting state."""
        client = MagicMock()
        client.issue.return_value = {
            "key": "TEST-1",
            "fields": {
                "status": {"name": "Open"},
                "issuetype": {"name": "Task", "id": "10001"},
            },
        }
        client.get.return_value = {
            "transitions": [
                {"id": "11", "name": "Start", "to": {"name": "In Progress"}},
                {"id": "21", "name": "Close", "to": {"name": "Done"}},
            ]
        }
        # After transitioning, report new state and no further transitions
        call_count = {"issue": 0, "get": 0}

        def issue_side_effect(key, **kwargs):
            call_count["issue"] += 1
            if call_count["issue"] <= 2:
                return {
                    "key": key,
                    "fields": {
                        "status": {"name": "Open"},
                        "issuetype": {"name": "Task", "id": "10001"},
                    },
                }
            return {"key": key, "fields": {"status": {"name": "In Progress"}}}

        def get_side_effect(url, **kwargs):
            call_count["get"] += 1
            if call_count["get"] == 1:
                return {
                    "transitions": [
                        {"id": "11", "name": "Start", "to": {"name": "In Progress"}},
                        {"id": "21", "name": "Close", "to": {"name": "Done"}},
                    ]
                }
            return {"transitions": []}

        client.issue.side_effect = issue_side_effect
        client.get.side_effect = get_side_effect
        client.set_issue_status.return_value = None

        graph = discover_workflow(client, "TEST-1")
        assert graph.issue_type == "Task"
        assert graph.issue_type_id == "10001"
        assert "Open" in graph.states
        assert len(graph.states["Open"]) == 2
        assert graph.discovered_from == "TEST-1"
        assert graph.discovered_at is not None
