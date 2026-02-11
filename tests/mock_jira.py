"""
Concrete mock Jira client for route tests.

NOT MagicMock — explicit methods that return fixture data for valid requests
and raise real requests.HTTPError for invalid ones. This ensures tests verify
actual route logic rather than MagicMock's permissive auto-attributes.
"""

import json
from copy import deepcopy

import requests

from .fixtures import (
    TEST_PROJECT,
    TEST_ISSUE,
    USER,
    ISSUE,
    ISSUE_WITH_COMMENTS,
    ISSUE_WITH_ATTACHMENTS,
    ISSUE_WITH_LINKS,
    CREATED_ISSUE,
    SEARCH_RESULTS,
    SEARCH_RESULTS_PAGE2,
    SEARCH_EMPTY,
    ADDED_COMMENT,
    TRANSITIONS,
    WATCHERS,
    WORKLOGS,
    ADDED_WORKLOG,
    PROJECTS,
    PROJECT,
    COMPONENTS,
    COMPONENT,
    CREATED_COMPONENT,
    VERSIONS,
    VERSION,
    CREATED_VERSION,
    PRIORITIES,
    STATUSES,
    FIELDS,
    FILTERS,
    FILTER,
    LINK_TYPES,
    WEBLINKS,
    ADDED_WEBLINK,
    UPLOADED_ATTACHMENT,
    BOARDS,
    SPRINTS,
    SPRINT,
)


def make_http_error(status_code: int, message: str = "") -> requests.HTTPError:
    """Create a real requests.HTTPError with a real Response object.

    This ensures get_status_code() and is_status() from response.py work correctly.
    """
    response = requests.Response()
    response.status_code = status_code
    response._content = json.dumps({"errorMessages": [message]}).encode()
    error = requests.HTTPError(message, response=response)
    return error


def _is_nonexistent(key: str) -> bool:
    """Check if a key/id represents a nonexistent resource."""
    if not key:
        return True
    key_upper = key.upper()
    return (
        "NONEXISTENT" in key_upper
        or key == "99999999"
        or key == "invalid-key-format"
        or key == "not-a-valid-key"
    )


def _is_forbidden(key: str) -> bool:
    """Check if a key/id should trigger a 403 Forbidden response."""
    if not key:
        return False
    return "FORBIDDEN" in key.upper()


class MockJiraClient:
    """Concrete mock Jira client implementing all methods used by route handlers."""

    def __init__(self):
        self.url = "https://jira.example.com"
        self._call_log: list[tuple] = []
        self._issue_statuses: dict[str, str] = {}  # Tracks status changes from set_issue_status

    # =========================================================================
    # User / Auth
    # =========================================================================

    def myself(self) -> dict:
        self._call_log.append(("myself",))
        return deepcopy(USER)

    # =========================================================================
    # Issues
    # =========================================================================

    def issue(self, key: str, **kwargs) -> dict:
        self._call_log.append(("issue", key, kwargs))

        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")

        fields = kwargs.get("fields", "")

        if fields == "comment":
            return deepcopy(ISSUE_WITH_COMMENTS)
        if fields == "attachment":
            return deepcopy(ISSUE_WITH_ATTACHMENTS)
        if fields == "issuelinks":
            return deepcopy(ISSUE_WITH_LINKS)
        if fields == "*all,comment":
            return deepcopy(ISSUE_WITH_COMMENTS)
        if fields == "status":
            status_name = self._issue_statuses.get(key, "Open")
            return {"key": key, "fields": {"status": {"name": status_name, "id": "1"}}}

        return deepcopy(ISSUE)

    def create_issue(self, fields: dict) -> dict:
        self._call_log.append(("create_issue", fields))
        return deepcopy(CREATED_ISSUE)

    def delete_issue(self, key: str) -> None:
        self._call_log.append(("delete_issue", key))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")

    def update_issue_field(self, key: str, fields: dict) -> None:
        self._call_log.append(("update_issue_field", key, fields))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")

    def set_issue_status(self, key: str, status_name: str) -> None:
        self._call_log.append(("set_issue_status", key, status_name))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")
        self._issue_statuses[key] = status_name

    # =========================================================================
    # Search
    # =========================================================================

    def jql(self, jql: str, limit: int = 50, start: int = 0, fields: list | None = None) -> dict:
        self._call_log.append(("jql", jql, {"limit": limit, "start": start, "fields": fields}))

        if "invalid" in jql.lower() or "!!!" in jql:
            raise make_http_error(400, "Invalid JQL query")

        if "NONEXISTENT" in jql:
            return deepcopy(SEARCH_EMPTY)

        if start > 0:
            result = deepcopy(SEARCH_RESULTS_PAGE2)
            result["startAt"] = start
            if limit:
                result["issues"] = result["issues"][:limit]
            return result

        result = deepcopy(SEARCH_RESULTS)
        if limit:
            result["issues"] = result["issues"][:limit]
        return result

    # =========================================================================
    # Comments
    # =========================================================================

    def issue_add_comment(self, key: str, text: str) -> dict:
        self._call_log.append(("issue_add_comment", key, text))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")
        result = deepcopy(ADDED_COMMENT)
        result["body"] = text
        return result

    def delete(self, url: str, **kwargs) -> None:
        """Generic delete method used by comments and weblinks."""
        self._call_log.append(("delete", url, kwargs))
        for part in url.split("/"):
            if _is_nonexistent(part):
                raise make_http_error(404, "Not found")

    # =========================================================================
    # Transitions / Workflow
    # =========================================================================

    def get_issue_transitions(self, key: str) -> list:
        self._call_log.append(("get_issue_transitions", key))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")
        return deepcopy(TRANSITIONS)

    # =========================================================================
    # Watchers
    # =========================================================================

    def issue_get_watchers(self, key: str) -> dict:
        self._call_log.append(("issue_get_watchers", key))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")
        return deepcopy(WATCHERS)

    def issue_add_watcher(self, key: str, username: str) -> None:
        self._call_log.append(("issue_add_watcher", key, username))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")

    def issue_delete_watcher(self, key: str, username: str) -> None:
        self._call_log.append(("issue_delete_watcher", key, username))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")

    # =========================================================================
    # Attachments
    # =========================================================================

    def add_attachment_object(self, issue_key: str, attachment) -> list:
        self._call_log.append(("add_attachment_object", issue_key, getattr(attachment, "name", None)))
        if _is_nonexistent(issue_key):
            raise make_http_error(404, f"Issue {issue_key} not found")
        result = deepcopy(UPLOADED_ATTACHMENT)
        if hasattr(attachment, "name") and attachment.name:
            result[0]["filename"] = attachment.name
        return result

    def delete_attachment(self, attachment_id: str) -> None:
        self._call_log.append(("delete_attachment", attachment_id))
        if _is_nonexistent(attachment_id):
            raise make_http_error(404, f"Attachment {attachment_id} not found")
        if _is_forbidden(attachment_id):
            raise make_http_error(403, "Permission denied")

    # =========================================================================
    # Projects
    # =========================================================================

    def projects(self, **kwargs) -> list:
        self._call_log.append(("projects", kwargs))
        return deepcopy(PROJECTS)

    def project(self, key: str) -> dict:
        self._call_log.append(("project", key))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Project {key} not found")
        result = deepcopy(PROJECT)
        result["key"] = key.upper()
        return result

    # =========================================================================
    # Components
    # =========================================================================

    def get_project_components(self, project: str) -> list:
        self._call_log.append(("get_project_components", project))
        if _is_nonexistent(project):
            raise make_http_error(404, f"Project {project} not found")
        return deepcopy(COMPONENTS)

    def create_component(self, component: dict) -> dict:
        self._call_log.append(("create_component", component))
        return deepcopy(CREATED_COMPONENT)

    def component(self, component_id: str) -> dict:
        self._call_log.append(("component", component_id))
        if _is_nonexistent(component_id):
            raise make_http_error(404, f"Component {component_id} not found")
        return deepcopy(COMPONENT)

    def delete_component(self, component_id: str) -> None:
        self._call_log.append(("delete_component", component_id))
        if _is_nonexistent(component_id):
            raise make_http_error(404, f"Component {component_id} not found")

    # =========================================================================
    # Versions
    # =========================================================================

    def get_project_versions(self, project: str) -> list:
        self._call_log.append(("get_project_versions", project))
        if _is_nonexistent(project):
            raise make_http_error(404, f"Project {project} not found")
        return deepcopy(VERSIONS)

    def create_version(self, name: str, project: str, description: str | None = None, released: bool = False) -> dict:
        self._call_log.append(("create_version", name, project))
        return deepcopy(CREATED_VERSION)

    def get_version(self, version_id: str) -> dict:
        self._call_log.append(("get_version", version_id))
        if _is_nonexistent(version_id):
            raise make_http_error(404, f"Version {version_id} not found")
        return deepcopy(VERSION)

    def update_version(self, version_id: str, **kwargs) -> dict:
        self._call_log.append(("update_version", version_id, kwargs))
        if _is_nonexistent(version_id):
            raise make_http_error(404, f"Version {version_id} not found")
        return deepcopy(VERSION)

    # =========================================================================
    # Priorities
    # =========================================================================

    def get_all_priorities(self) -> list:
        self._call_log.append(("get_all_priorities",))
        return deepcopy(PRIORITIES)

    # =========================================================================
    # Statuses
    # =========================================================================

    def get_all_statuses(self) -> list:
        self._call_log.append(("get_all_statuses",))
        return deepcopy(STATUSES)

    # =========================================================================
    # Fields
    # =========================================================================

    def get_all_fields(self) -> list:
        self._call_log.append(("get_all_fields",))
        return deepcopy(FIELDS)

    # =========================================================================
    # Filters
    # =========================================================================

    def get_filter(self, filter_id: str) -> dict:
        self._call_log.append(("get_filter", filter_id))
        if _is_nonexistent(filter_id):
            raise make_http_error(404, f"Filter {filter_id} not found")
        result = deepcopy(FILTER)
        result["id"] = filter_id
        return result

    # =========================================================================
    # Link Types
    # =========================================================================

    def get_issue_link_types(self) -> list:
        self._call_log.append(("get_issue_link_types",))
        return deepcopy(LINK_TYPES)

    def create_issue_link(self, link_data: dict) -> None:
        self._call_log.append(("create_issue_link", link_data))

    # =========================================================================
    # Worklogs
    # =========================================================================

    def issue_get_worklog(self, key: str) -> dict:
        self._call_log.append(("issue_get_worklog", key))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")
        return deepcopy(WORKLOGS)

    def issue_add_json_worklog(self, key: str, worklog: dict) -> dict:
        self._call_log.append(("issue_add_json_worklog", key, worklog))
        if _is_nonexistent(key):
            raise make_http_error(404, f"Issue {key} not found")
        return deepcopy(ADDED_WORKLOG)

    # =========================================================================
    # Agile / Generic HTTP
    # =========================================================================

    def get(self, url: str, **kwargs) -> dict | list:
        """Generic GET used by agile routes, worklogs, filters, and weblinks."""
        self._call_log.append(("get", url, kwargs))

        if "filter/favourite" in url:
            return deepcopy(FILTERS)
        if "remotelink" in url:
            for part in url.split("/"):
                if part and _is_nonexistent(part):
                    raise make_http_error(404, "Issue not found")
            return deepcopy(WEBLINKS)
        if "agile" in url and "board" in url:
            # Check for nonexistent board ID in URL
            parts = url.split("/")
            for i, part in enumerate(parts):
                if part == "board" and i + 1 < len(parts):
                    board_id = parts[i + 1]
                    if board_id.isdigit() and _is_nonexistent(board_id):
                        raise make_http_error(404, f"Board {board_id} not found")
            if "sprint" in url:
                return deepcopy(SPRINTS)
            return deepcopy(BOARDS)
        if "agile" in url and "sprint" in url:
            # Check for nonexistent sprint ID in URL
            parts = url.split("/")
            for i, part in enumerate(parts):
                if part == "sprint" and i + 1 < len(parts):
                    sprint_id = parts[i + 1]
                    if sprint_id.isdigit() and _is_nonexistent(sprint_id):
                        raise make_http_error(404, f"Sprint {sprint_id} not found")
            return deepcopy(SPRINT)
        if "worklog" in url:
            parts = url.split("/")
            for part in parts:
                if _is_nonexistent(part):
                    raise make_http_error(404, "Not found")
            return deepcopy(ADDED_WORKLOG)

        return {}

    def post(self, url: str, **kwargs) -> dict:
        """Generic POST used by agile routes and weblinks."""
        self._call_log.append(("post", url, kwargs))

        if "remotelink" in url:
            return deepcopy(ADDED_WEBLINK)

        return {"success": True}
