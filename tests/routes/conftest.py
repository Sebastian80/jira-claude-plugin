"""Pytest configuration for Jira plugin route tests.

TestClient-based tests — no server process needed.
"""

import sys
from pathlib import Path

import pytest

# Add tests directory to path for helpers import
sys.path.insert(0, str(Path(__file__).parent))

from helpers import reset_mock_client


@pytest.fixture(autouse=True)
def _fresh_mock_client():
    """Reset mock client state before each test to prevent cross-test contamination."""
    reset_mock_client()
