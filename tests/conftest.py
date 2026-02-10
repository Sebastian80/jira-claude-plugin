"""
Pytest fixtures for jira plugin tests.

Fixtures here are used by unit tests (tests/unit/test_formatters.py).
Route tests use MockJiraClient via tests/routes/helpers.py instead.
"""

import sys
from pathlib import Path

import pytest

# Add plugin root to path
PLUGIN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))


@pytest.fixture
def sample_issue():
    """Sample Jira issue data."""
    return {
        "key": "TEST-123",
        "fields": {
            "summary": "Sample test issue summary",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "John Doe"},
            "description": "This is a detailed description of the issue.",
        },
    }


@pytest.fixture
def sample_search_results():
    """Sample search results."""
    return [
        {
            "key": "TEST-1",
            "fields": {
                "summary": "First test issue",
                "status": {"name": "Open"},
                "priority": {"name": "High"},
            },
        },
        {
            "key": "TEST-2",
            "fields": {
                "summary": "Second test issue",
                "status": {"name": "Closed"},
                "priority": {"name": "Low"},
            },
        },
    ]


@pytest.fixture
def sample_transitions():
    """Sample transitions list."""
    return [
        {"id": "11", "name": "Start Progress", "to": "In Progress"},
        {"id": "21", "name": "Resolve", "to": "Resolved"},
        {"id": "31", "name": "Close", "to": "Done"},
    ]


@pytest.fixture
def sample_comments():
    """Sample comments list."""
    return [
        {
            "id": "1001",
            "author": {"displayName": "Alice"},
            "body": "This is a test comment from Alice.",
            "created": "2024-01-15T10:30:00.000+0000",
        },
        {
            "id": "1002",
            "author": {"displayName": "Bob"},
            "body": "Another comment from Bob.",
            "created": "2024-01-16T14:45:00.000+0000",
        },
    ]
