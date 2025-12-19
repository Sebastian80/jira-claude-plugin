"""Pytest configuration for Jira plugin tests.

This file configures pytest options and fixtures. Shared helper functions
are in helpers.py to avoid import issues.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Add tests directory to path for helpers import
sys.path.insert(0, str(Path(__file__).parent))

# Plugin and CLI paths
PLUGIN_DIR = Path(__file__).parent.parent.parent
JIRA_CMD = str(PLUGIN_DIR / "bin" / "jira")


# ==============================================================================
# Pytest Hooks
# ==============================================================================

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-write-tests",
        action="store_true",
        default=False,
        help="Run tests that modify Jira data (create issues, comments, etc.)"
    )


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "write_test: marks tests that modify Jira data"
    )


def pytest_collection_modifyitems(config, items):
    """Skip write tests unless --run-write-tests is passed."""
    if config.getoption("--run-write-tests"):
        # Don't skip write tests
        return

    skip_write = pytest.mark.skip(reason="Write test - run with --run-write-tests")
    for item in items:
        if "write_test" in item.keywords:
            item.add_marker(skip_write)


@pytest.fixture(scope="session", autouse=True)
def ensure_server_running():
    """Ensure jira server is running before tests."""
    # Check if server is already running via status command
    result = subprocess.run(
        [JIRA_CMD, "status"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or "not running" in result.stdout.lower():
        # Try to start the server
        start_result = subprocess.run(
            [JIRA_CMD, "start"],
            capture_output=True,
            text=True
        )
        if start_result.returncode != 0:
            pytest.skip(f"Failed to start jira server: {start_result.stderr}")

    # Verify health
    health_result = subprocess.run(
        [JIRA_CMD, "health"],
        capture_output=True,
        text=True
    )
    if "unhealthy" in health_result.stdout.lower():
        pytest.skip("Jira server unhealthy - check credentials in ~/.env.jira")
