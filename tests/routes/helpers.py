"""
Shared test helpers for Jira plugin tests.

This module provides common utilities and configuration for all test files.
"""

import json
import subprocess
from pathlib import Path

import pytest


# ==============================================================================
# Test Configuration
# ==============================================================================

TEST_PROJECT = "HMKG"  # Project with test issues
TEST_ISSUE = "HMKG-2062"  # Existing issue for read tests

# Jira CLI path - use the standalone jira CLI
PLUGIN_DIR = Path(__file__).parent.parent.parent
JIRA_CMD = str(PLUGIN_DIR / "bin" / "jira")


# ==============================================================================
# CLI Helper Functions
# ==============================================================================

def run_cli(*args, expect_success=True) -> dict | list | str:
    """Run jira CLI command and return parsed result.

    Args:
        *args: Command arguments to pass to jira (e.g., "issue", "PROJ-123")
        expect_success: If True, fail test on error responses

    Returns:
        Parsed JSON response or raw output string
    """
    args_list = list(args)
    # Strip redundant "jira" prefix - tests call run_cli("jira", "cmd") but CLI is already jira
    if args_list and args_list[0] == "jira":
        args_list = args_list[1:]
    # Add --format json to get parseable output
    if "--format" not in args_list:
        args_list.extend(["--format", "json"])
    cmd = [JIRA_CMD] + args_list
    result = subprocess.run(cmd, capture_output=True, text=True)

    output = result.stdout.strip()
    if not output:
        output = result.stderr.strip()

    try:
        parsed = json.loads(output)
        if expect_success and isinstance(parsed, dict):
            # Check for error responses
            if parsed.get("success") is False:
                pytest.fail(f"Command failed: {parsed.get('error')}")
            if "detail" in parsed:  # FastAPI validation error
                pytest.fail(f"Validation error: {parsed['detail']}")
        return parsed
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
        *args: Command arguments to pass to jira

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    args_list = list(args)
    # Strip redundant "jira" prefix
    if args_list and args_list[0] == "jira":
        args_list = args_list[1:]
    cmd = [JIRA_CMD] + args_list
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode
