"""
Shared test helpers for Jira plugin tests.

Uses FastAPI TestClient with dependency override to test routes
without subprocess calls or a running server.
"""

import json
import io
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from jira.main import app
from jira.deps import jira
from tests.mock_jira import MockJiraClient


# ==============================================================================
# Test Configuration
# ==============================================================================

TEST_PROJECT = "HMKG"  # Project with test issues
TEST_ISSUE = "HMKG-2062"  # Existing issue for read tests

# Plugin directory (for reference only — no subprocess use)
PLUGIN_DIR = Path(__file__).parent.parent.parent


# ==============================================================================
# TestClient Setup
# ==============================================================================

_mock_client = MockJiraClient()


def _get_mock_jira():
    return _mock_client


# Override the jira dependency with our mock
app.dependency_overrides[jira] = _get_mock_jira

_test_client = TestClient(app, raise_server_exceptions=False)


def get_mock_client() -> MockJiraClient:
    """Get the current mock client for call verification in write tests."""
    return _mock_client


def reset_mock_client():
    """Reset mock client state (call log) between tests if needed."""
    global _mock_client
    _mock_client = MockJiraClient()
    app.dependency_overrides[jira] = lambda: _mock_client


# ==============================================================================
# CLI Argument Routing (replicates bin/jira logic in Python)
# ==============================================================================

# HTTP method detection by endpoint name (mirrors bin/jira get_method_for_endpoint)
_POST_ENDPOINTS = {"create", "comment", "transition", "worklog", "attachment", "watcher", "weblink", "link"}
_PATCH_ENDPOINTS = {"update"}
_DELETE_ENDPOINTS = {"delete"}

# Endpoint aliases (mirrors bin/jira get_endpoint_alias)
_ENDPOINT_ALIASES = {
    "update": "issue",
}


def _get_method(endpoint: str) -> str:
    """Determine HTTP method from endpoint name."""
    if endpoint in _POST_ENDPOINTS:
        return "POST"
    if endpoint in _PATCH_ENDPOINTS:
        return "PATCH"
    if endpoint in _DELETE_ENDPOINTS:
        return "DELETE"
    return "GET"


def _parse_cli_args(args: list[str]) -> dict:
    """Parse CLI-style arguments into request parameters.

    Replicates bin/jira route_request arg parsing:
    - First arg is endpoint
    - Positional args become path segments
    - --key value becomes query or body params
    - --file path becomes multipart upload
    - -X METHOD overrides HTTP method
    """
    args = list(args)

    # Strip redundant "jira" prefix
    if args and args[0] == "jira":
        args = args[1:]

    if not args:
        return {"endpoint": "help", "path_args": [], "params": {}, "method_override": None, "file_path": None}

    endpoint = args[0]
    remaining = args[1:]

    path_args = []
    params = {}
    method_override = None
    file_path = None

    i = 0
    while i < len(remaining):
        arg = remaining[i]
        if arg == "--file":
            if i + 1 < len(remaining):
                file_path = remaining[i + 1]
                i += 2
            else:
                i += 1
        elif arg == "-X":
            if i + 1 < len(remaining):
                method_override = remaining[i + 1]
                i += 2
            else:
                i += 1
        elif arg.startswith("--"):
            key = arg[2:]
            if "=" in key:
                k, v = key.split("=", 1)
                params[k] = v
            elif i + 1 < len(remaining) and not remaining[i + 1].startswith("--"):
                params[key] = remaining[i + 1]
                i += 2
                continue
            else:
                params[key] = "true"
            i += 1
        else:
            path_args.append(arg)
            i += 1

    return {
        "endpoint": endpoint,
        "path_args": path_args,
        "params": params,
        "method_override": method_override,
        "file_path": file_path,
    }


def _build_request(parsed: dict) -> tuple[str, str, dict | None, dict | None, dict | None]:
    """Build HTTP request from parsed CLI args.

    Returns: (method, url, query_params, json_body, files)
    """
    endpoint = parsed["endpoint"]
    path_args = parsed["path_args"]
    params = parsed["params"]
    method_override = parsed["method_override"]
    file_path = parsed["file_path"]

    # Handle help command: route to /jira/help/...
    if endpoint in ("help", "--help", "-h"):
        url = "/jira/help"
        for arg in path_args:
            url += f"/{quote(arg, safe='')}"
        query_params = {k: v for k, v in params.items()}
        return "GET", url, query_params, None, None

    # Resolve endpoint alias
    actual_endpoint = _ENDPOINT_ALIASES.get(endpoint, endpoint)

    # Determine HTTP method
    method = method_override if method_override else _get_method(endpoint)

    # Build URL
    url = f"/jira/{actual_endpoint}"
    for arg in path_args:
        url += f"/{quote(arg, safe='')}"

    # Split params into query vs body based on method
    if method in ("POST", "PATCH"):
        query_params = {}
        body_params = {}
        for key, value in params.items():
            if key == "format":
                query_params[key] = value
            else:
                body_params[key] = value

        if file_path:
            # Multipart file upload
            return method, url, query_params, None, {"file_path": file_path}
        elif body_params:
            return method, url, query_params, body_params, None
        else:
            return method, url, query_params, None, None
    else:
        # GET/DELETE: all params as query string
        return method, url, params, None, None


def _execute_request(method: str, url: str, query_params: dict | None = None,
                     json_body: dict | None = None, files: dict | None = None):
    """Execute HTTP request via TestClient."""
    kwargs = {}
    if query_params:
        kwargs["params"] = query_params
    if json_body:
        kwargs["json"] = json_body

    if files and files.get("file_path"):
        fp = files["file_path"]
        file_content = Path(fp).read_bytes() if Path(fp).exists() else b"mock file content"
        filename = Path(fp).name
        kwargs["files"] = {"file": (filename, io.BytesIO(file_content), "application/octet-stream")}

    if method == "GET":
        return _test_client.get(url, **kwargs)
    elif method == "POST":
        return _test_client.post(url, **kwargs)
    elif method == "PATCH":
        return _test_client.patch(url, **kwargs)
    elif method == "DELETE":
        return _test_client.delete(url, **kwargs)
    else:
        return _test_client.get(url, **kwargs)


# ==============================================================================
# CLI Helper Functions (public API matching original interface)
# ==============================================================================

def run_cli(*args, expect_success=True) -> dict | list | str:
    """Run jira CLI command and return parsed result.

    Args:
        *args: Command arguments (e.g., "issue", "PROJ-123")
        expect_success: If True, fail test on error responses

    Returns:
        Parsed JSON response or raw output string
    """
    args_list = list(args)

    # Strip redundant "jira" prefix
    if args_list and args_list[0] == "jira":
        args_list = args_list[1:]

    # Handle "status" with no args (server management, not API)
    if args_list == ["status"]:
        return f"Server running (TestClient) on mock://localhost"

    # Handle "--help" suffix: route to help endpoint
    if args_list and args_list[-1] == "--help":
        # e.g. ["priorities", "--help"] -> help for priorities
        endpoint = args_list[0] if len(args_list) > 1 else ""
        args_list = ["help", endpoint] if endpoint else ["help"]

    # Add --format json to get parseable output
    if "--format" not in args_list:
        args_list.extend(["--format", "json"])

    parsed = _parse_cli_args(args_list)
    method, url, query_params, json_body, files = _build_request(parsed)
    response = _execute_request(method, url, query_params, json_body, files)

    output = response.text.strip()

    try:
        parsed_json = json.loads(output)
        if expect_success and isinstance(parsed_json, dict):
            if parsed_json.get("success") is False:
                pytest.fail(f"Command failed: {parsed_json.get('error')}")
            if "detail" in parsed_json:
                pytest.fail(f"Validation error: {parsed_json['detail']}")
        return parsed_json
    except json.JSONDecodeError:
        return output


def get_data(result) -> list | dict | str:
    """Extract data from API response, handling both wrapped and direct formats.

    Args:
        result: API response (dict with 'data' key, list, or str)

    Returns:
        Unwrapped data
    """
    if isinstance(result, dict):
        return result.get("data", result)
    return result  # Already unwrapped (list or str)


def run_cli_raw(*args) -> tuple[str, str, int]:
    """Run jira CLI and return raw stdout, stderr, returncode.

    Args:
        *args: Command arguments

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    args_list = list(args)

    # Strip redundant "jira" prefix
    if args_list and args_list[0] == "jira":
        args_list = args_list[1:]

    # Handle "status" with no args (server management, not API)
    if args_list == ["status"]:
        return "Server running (TestClient) on mock://localhost\npid: 99999", "", 0

    # Handle "--help" suffix: route to help endpoint
    if args_list and args_list[-1] == "--help":
        endpoint = args_list[0] if len(args_list) > 1 else ""
        args_list = ["help", endpoint] if endpoint else ["help"]
        # Ensure --format is present for help requests
        if "--format" not in args_list:
            args_list.extend(["--format", "json"])

    parsed = _parse_cli_args(args_list)
    method, url, query_params, json_body, files = _build_request(parsed)
    response = _execute_request(method, url, query_params, json_body, files)

    stdout = response.text
    stderr = ""
    returncode = 0 if 200 <= response.status_code < 300 else 1

    return stdout, stderr, returncode
