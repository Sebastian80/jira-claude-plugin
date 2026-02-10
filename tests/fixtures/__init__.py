"""
Mock fixture data for Jira plugin tests.

Contains minimal but structurally complete response data for all Jira types.
Each fixture has the fields that existing test assertions check.
"""

# Test constants matching helpers.py
TEST_PROJECT = "HMKG"
TEST_ISSUE = "HMKG-2062"

# =============================================================================
# User / Auth
# =============================================================================

USER = {
    "name": "test.user",
    "displayName": "Test User",
    "emailAddress": "test.user@example.com",
    "accountId": "abc123",
    "active": True,
}

# =============================================================================
# Issues
# =============================================================================

ISSUE = {
    "key": TEST_ISSUE,
    "id": "10001",
    "self": f"https://jira.example.com/rest/api/2/issue/10001",
    "fields": {
        "summary": "Test issue for mock suite",
        "status": {"name": "Open", "id": "1"},
        "issuetype": {"name": "Task", "id": "10001"},
        "priority": {"name": "High", "id": "2"},
        "assignee": {"displayName": "Test User", "name": "test.user"},
        "reporter": {"displayName": "Test User", "name": "test.user"},
        "description": "This is a test issue description.",
        "project": {"key": TEST_PROJECT, "name": "Test Project"},
    },
}

ISSUE_WITH_COMMENTS = {
    **ISSUE,
    "fields": {
        **ISSUE["fields"],
        "comment": {
            "comments": [
                {
                    "id": "10100",
                    "author": {"displayName": "Alice", "name": "alice"},
                    "body": "First comment from Alice.",
                    "created": "2024-01-15T10:30:00.000+0000",
                    "updated": "2024-01-15T10:30:00.000+0000",
                },
                {
                    "id": "10101",
                    "author": {"displayName": "Bob", "name": "bob"},
                    "body": "Second comment from Bob.",
                    "created": "2024-01-16T14:45:00.000+0000",
                    "updated": "2024-01-16T14:45:00.000+0000",
                },
            ],
            "maxResults": 2,
            "total": 2,
            "startAt": 0,
        },
    },
}

ISSUE_WITH_ATTACHMENTS = {
    **ISSUE,
    "fields": {
        **ISSUE["fields"],
        "attachment": [
            {
                "id": "10200",
                "filename": "test-file.txt",
                "self": f"https://jira.example.com/rest/api/2/attachment/10200",
                "size": 1024,
                "mimeType": "text/plain",
                "created": "2024-01-15T10:00:00.000+0000",
                "author": {"displayName": "Test User", "name": "test.user"},
            },
        ],
    },
}

ISSUE_WITH_LINKS = {
    **ISSUE,
    "fields": {
        **ISSUE["fields"],
        "issuelinks": [
            {
                "id": "10300",
                "type": {
                    "name": "Blocks",
                    "inward": "is blocked by",
                    "outward": "blocks",
                },
                "outwardIssue": {
                    "key": "HMKG-2063",
                    "fields": {"summary": "Linked issue", "status": {"name": "Open"}},
                },
            },
        ],
    },
}

CREATED_ISSUE = {"id": "10099", "key": "HMKG-9999", "self": "https://jira.example.com/rest/api/2/issue/10099"}

# =============================================================================
# Search
# =============================================================================

SEARCH_RESULTS = {
    "issues": [
        {
            "key": "HMKG-2062",
            "fields": {
                "summary": "Test issue for mock suite",
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "assignee": {"displayName": "Test User"},
                "issuetype": {"name": "Task"},
            },
        },
        {
            "key": "HMKG-2063",
            "fields": {
                "summary": "Second test issue",
                "status": {"name": "In Progress"},
                "priority": {"name": "Medium"},
                "assignee": {"displayName": "Alice"},
                "issuetype": {"name": "Bug"},
            },
        },
        {
            "key": "HMKG-2064",
            "fields": {
                "summary": "Third test issue",
                "status": {"name": "Done"},
                "priority": {"name": "Low"},
                "assignee": None,
                "issuetype": {"name": "Story"},
            },
        },
    ],
    "total": 3,
    "maxResults": 50,
    "startAt": 0,
}

SEARCH_RESULTS_PAGE2 = {
    "issues": [
        {
            "key": "HMKG-2065",
            "fields": {
                "summary": "Fourth test issue",
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "assignee": None,
                "issuetype": {"name": "Task"},
            },
        },
    ],
    "total": 4,
    "maxResults": 50,
    "startAt": 3,
}

SEARCH_EMPTY = {"issues": [], "total": 0, "maxResults": 50, "startAt": 0}

# =============================================================================
# Comments
# =============================================================================

ADDED_COMMENT = {
    "id": "10102",
    "self": f"https://jira.example.com/rest/api/2/issue/{TEST_ISSUE}/comment/10102",
    "author": {"displayName": "Test User", "name": "test.user"},
    "body": "[TEST] Auto-generated comment",
    "created": "2024-02-01T12:00:00.000+0000",
}

# =============================================================================
# Transitions / Workflow
# =============================================================================

TRANSITIONS = [
    {"id": "11", "name": "Start Progress", "to": "In Progress"},
    {"id": "21", "name": "Close", "to": "Done"},
    {"id": "31", "name": "Resolve", "to": "Resolved"},
]

# =============================================================================
# Watchers
# =============================================================================

WATCHERS = {
    "watchCount": 2,
    "isWatching": True,
    "watchers": [
        {"name": "test.user", "displayName": "Test User", "accountId": "abc123"},
        {"name": "alice", "displayName": "Alice", "accountId": "def456"},
    ],
}

# =============================================================================
# Worklogs
# =============================================================================

WORKLOGS = {
    "worklogs": [
        {
            "id": "10400",
            "author": {"displayName": "Test User", "name": "test.user"},
            "timeSpent": "2h",
            "timeSpentSeconds": 7200,
            "comment": "Worked on implementation",
            "started": "2024-01-15T09:00:00.000+0000",
            "created": "2024-01-15T11:00:00.000+0000",
        },
    ],
}

ADDED_WORKLOG = {
    "id": "10401",
    "author": {"displayName": "Test User", "name": "test.user"},
    "timeSpent": "1h",
    "timeSpentSeconds": 3600,
    "started": "2024-02-01T09:00:00.000+0000",
    "created": "2024-02-01T10:00:00.000+0000",
}

# =============================================================================
# Projects
# =============================================================================

PROJECTS = [
    {"key": TEST_PROJECT, "name": "Test Project", "id": "10000", "projectTypeKey": "software"},
    {"key": "OROSPD", "name": "OroSPD", "id": "10001", "projectTypeKey": "software"},
]

PROJECT = {
    "key": TEST_PROJECT,
    "name": "Test Project",
    "id": "10000",
    "description": "Test project for Jira CLI",
    "projectTypeKey": "software",
    "lead": {"displayName": "Test User", "name": "test.user"},
}

# =============================================================================
# Components
# =============================================================================

COMPONENTS = [
    {"id": "10500", "name": "Backend", "description": "Backend component", "project": TEST_PROJECT},
    {"id": "10501", "name": "Frontend", "description": "Frontend component", "project": TEST_PROJECT},
]

COMPONENT = {"id": "10500", "name": "Backend", "description": "Backend component", "project": TEST_PROJECT}

CREATED_COMPONENT = {"id": "10502", "name": "[TEST] New Component", "project": TEST_PROJECT}

# =============================================================================
# Versions
# =============================================================================

VERSIONS = [
    {"id": "10600", "name": "1.0.0", "released": True, "projectId": 10000},
    {"id": "10601", "name": "2.0.0", "released": False, "projectId": 10000},
]

VERSION = {"id": "10600", "name": "1.0.0", "released": True, "projectId": 10000, "description": "Initial release"}

CREATED_VERSION = {"id": "10602", "name": "[TEST] New Version", "released": False, "projectId": 10000}

# =============================================================================
# Priorities
# =============================================================================

PRIORITIES = [
    {"id": "1", "name": "Highest"},
    {"id": "2", "name": "High"},
    {"id": "3", "name": "Medium"},
    {"id": "4", "name": "Low"},
    {"id": "5", "name": "Lowest"},
]

# =============================================================================
# Statuses
# =============================================================================

STATUSES = [
    {"id": "1", "name": "Open", "statusCategory": {"name": "To Do"}},
    {"id": "3", "name": "In Progress", "statusCategory": {"name": "In Progress"}},
    {"id": "4", "name": "Resolved", "statusCategory": {"name": "Done"}},
    {"id": "5", "name": "Done", "statusCategory": {"name": "Done"}},
    {"id": "6", "name": "Closed", "statusCategory": {"name": "Done"}},
    {"id": "10000", "name": "To Do", "statusCategory": {"name": "To Do"}},
]

# =============================================================================
# Fields
# =============================================================================

FIELDS = [
    {"id": "summary", "name": "Summary", "custom": False, "schema": {"type": "string"}},
    {"id": "description", "name": "Description", "custom": False, "schema": {"type": "string"}},
    {"id": "status", "name": "Status", "custom": False, "schema": {"type": "status"}},
    {"id": "assignee", "name": "Assignee", "custom": False, "schema": {"type": "user"}},
    {"id": "reporter", "name": "Reporter", "custom": False, "schema": {"type": "user"}},
    {"id": "priority", "name": "Priority", "custom": False, "schema": {"type": "priority"}},
    {"id": "issuetype", "name": "Issue Type", "custom": False, "schema": {"type": "issuetype"}},
    {"id": "customfield_10001", "name": "Sprint", "custom": True, "schema": {"type": "array"}},
    {"id": "customfield_10002", "name": "Story Points", "custom": True, "schema": {"type": "number"}},
]

# =============================================================================
# Filters
# =============================================================================

FILTERS = [
    {"id": "10800", "name": "My Open Issues", "jql": "assignee = currentUser() AND resolution = Unresolved"},
    {"id": "10801", "name": "Recent Activity", "jql": "updated >= -7d ORDER BY updated DESC"},
]

FILTER = {
    "id": "10800",
    "name": "My Open Issues",
    "jql": "assignee = currentUser() AND resolution = Unresolved",
    "owner": {"displayName": "Test User", "name": "test.user"},
}

# =============================================================================
# Link Types
# =============================================================================

LINK_TYPES = [
    {"id": "10000", "name": "Blocks", "inward": "is blocked by", "outward": "blocks"},
    {"id": "10001", "name": "Cloners", "inward": "is cloned by", "outward": "clones"},
    {"id": "10002", "name": "Duplicate", "inward": "is duplicated by", "outward": "duplicates"},
    {"id": "10003", "name": "Relates", "inward": "relates to", "outward": "relates to"},
]

# =============================================================================
# Web Links (Remote Links)
# =============================================================================

WEBLINKS = [
    {
        "id": 10900,
        "self": f"https://jira.example.com/rest/api/2/issue/{TEST_ISSUE}/remotelink/10900",
        "object": {"url": "https://example.com", "title": "Example Website"},
    },
]

ADDED_WEBLINK = {"id": 10901, "self": f"https://jira.example.com/rest/api/2/issue/{TEST_ISSUE}/remotelink/10901"}

# =============================================================================
# Attachments
# =============================================================================

UPLOADED_ATTACHMENT = [
    {
        "id": "10200",
        "filename": "test-upload.txt",
        "self": f"https://jira.example.com/rest/api/2/attachment/10200",
        "size": 100,
        "mimeType": "text/plain",
    },
]

# =============================================================================
# Agile (Boards / Sprints)
# =============================================================================

BOARDS = {
    "values": [
        {"id": 1, "name": "HMKG Board", "type": "scrum"},
        {"id": 2, "name": "OROSPD Board", "type": "kanban"},
    ],
}

SPRINTS = {
    "values": [
        {"id": 100, "name": "Sprint 1", "state": "active", "originBoardId": 1},
        {"id": 101, "name": "Sprint 2", "state": "future", "originBoardId": 1},
    ],
}

SPRINT = {"id": 100, "name": "Sprint 1", "state": "active", "originBoardId": 1}
