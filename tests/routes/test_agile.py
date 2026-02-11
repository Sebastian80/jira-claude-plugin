"""
Tests for Agile/Sprint endpoints.

Endpoints tested:
- GET /boards - List boards
- GET /sprints/{board_id} - List sprints for a board
- GET /sprint/{sprint_id} - Get sprint details
- GET /sprint/active/{project} - Get active sprint for project
- POST /sprint/{sprint_id}/issues - Add issues to sprint
- DELETE /sprint/{sprint_id}/issues - Remove issues from sprint
"""

import json

import pytest

from helpers import TEST_PROJECT, run_cli, get_data, run_cli_raw


class TestListBoards:
    """Test /boards endpoint."""

    def test_list_boards_basic(self):
        """Should list all boards."""
        result = run_cli("jira", "boards")
        data = get_data(result)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_boards_has_name_and_type(self):
        """Each board should have id, name, and type."""
        result = run_cli("jira", "boards")
        data = get_data(result)
        board = data[0]
        assert "id" in board
        assert "name" in board
        assert "type" in board

    def test_list_boards_filter_by_project(self):
        """Should accept project filter parameter."""
        result = run_cli("jira", "boards", "--project", TEST_PROJECT)
        data = get_data(result)
        assert isinstance(data, list)

    def test_list_boards_filter_by_type(self):
        """Should accept type filter parameter."""
        result = run_cli("jira", "boards", "--type", "scrum")
        data = get_data(result)
        assert isinstance(data, list)


class TestListSprints:
    """Test /sprints/{board_id} endpoint."""

    def test_list_sprints_basic(self):
        """Should list sprints for a board."""
        result = run_cli("jira", "sprints", "1")
        data = get_data(result)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_sprints_has_fields(self):
        """Each sprint should have id, name, state."""
        result = run_cli("jira", "sprints", "1")
        data = get_data(result)
        sprint = data[0]
        assert "id" in sprint
        assert "name" in sprint
        assert "state" in sprint

    def test_list_sprints_filter_by_state(self):
        """Should accept state filter parameter."""
        result = run_cli("jira", "sprints", "1", "--state", "active")
        data = get_data(result)
        assert isinstance(data, list)


class TestGetSprint:
    """Test /sprint/{sprint_id} endpoint."""

    def test_get_sprint_basic(self):
        """Should return sprint details."""
        result = run_cli("jira", "sprint", "100")
        data = get_data(result)
        assert isinstance(data, dict)
        assert "id" in data
        assert "name" in data


class TestGetActiveSprint:
    """Test /sprint/active/{project} endpoint."""

    def test_get_active_sprint_basic(self):
        """Should return the active sprint for a project."""
        result = run_cli("jira", "sprint", "active", TEST_PROJECT)
        data = get_data(result)
        assert isinstance(data, dict)
        assert "id" in data
        assert "state" in data


class TestAddIssuesToSprint:
    """Test POST /sprint/{sprint_id}/issues endpoint."""

    def test_add_single_issue(self):
        """Should add a single issue to sprint."""
        stdout, stderr, code = run_cli_raw(
            "jira", "sprint", "100", "issues", "--issues", "HMKG-2062", "-X", "POST"
        )
        assert code == 0
        data = json.loads(stdout)
        assert data.get("success") is True

    def test_add_multiple_issues(self):
        """Should add comma-separated issues to sprint."""
        stdout, stderr, code = run_cli_raw(
            "jira", "sprint", "100", "issues", "--issues", "HMKG-2062,HMKG-2063", "-X", "POST"
        )
        assert code == 0
        data = json.loads(stdout)
        result = data.get("data", data)
        assert "added" in result
        assert len(result["added"]) == 2


class TestRemoveIssuesFromSprint:
    """Test DELETE /sprint/{sprint_id}/issues endpoint."""

    def test_remove_issues(self):
        """Should remove issues from sprint (move to backlog)."""
        stdout, stderr, code = run_cli_raw(
            "jira", "sprint", "100", "issues", "--issues", "HMKG-2062", "-X", "DELETE"
        )
        assert code == 0
        data = json.loads(stdout)
        result = data.get("data", data)
        assert "moved_to_backlog" in result


class TestAgileHTTPErrors:
    """Test that agile routes handle HTTPError properly (bug 4.4)."""

    def test_sprints_nonexistent_board_returns_friendly_error(self):
        """Should return user-friendly error, not generic 500 detail."""
        from helpers import _test_client
        response = _test_client.get("/jira/sprints/99999999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_sprint_nonexistent_returns_friendly_error(self):
        """Should return user-friendly error, not generic 500 detail."""
        from helpers import _test_client
        response = _test_client.get("/jira/sprint/99999999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()


class TestAgileEdgeCases:
    """Test edge cases for agile endpoints."""

    def test_boards_returns_list(self):
        """Boards should always return a list."""
        result = run_cli("jira", "boards")
        data = get_data(result)
        assert isinstance(data, list)

    def test_sprints_invalid_board(self):
        """Non-integer board_id should return validation error."""
        stdout, stderr, code = run_cli_raw("jira", "sprints", "not-a-number")
        # FastAPI will return 422 for invalid path parameter type
        assert code != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
