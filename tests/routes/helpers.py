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

TEST_PROJECT = "OROSPD"  # Project with test issues
TEST_ISSUE = "OROSPD-589"  # Existing issue for read tests

# Bridge CLI path (avoid collision with /usr/sbin/bridge)
_BRIDGE_VENV = Path.home() / ".claude/plugins/marketplaces/sebastian-marketplace/plugins/ai-tool-bridge/.venv"
BRIDGE_CMD = str(_BRIDGE_VENV / "bin/bridge")


# ==============================================================================
# CLI Helper Functions
# ==============================================================================

def run_cli(*args, expect_success=True) -> dict | list | str:
    """Run bridge CLI command and return parsed result.

    Args:
        *args: Command arguments to pass to bridge (e.g., "jira", "user")
        expect_success: If True, fail test on error responses

    Returns:
        Parsed JSON response or raw output string
    """
    # Add --format json to get parseable output
    args_list = list(args)
    if "--format" not in args_list:
        args_list.extend(["--format", "json"])
    cmd = [BRIDGE_CMD] + args_list
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
    """Run bridge CLI and return raw stdout, stderr, returncode.

    Args:
        *args: Command arguments to pass to bridge

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    cmd = [BRIDGE_CMD] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode
