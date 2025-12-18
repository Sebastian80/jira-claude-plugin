"""
Jira Tools - Pydantic-based tool definitions.

All Jira operations as Tool classes for use with the bridge tools framework.
"""

from .issues import CreateIssue, GetIssue, UpdateIssue
from .search import SearchIssues
from .comments import AddComment, GetComments
from .workflow import GetTransitions, Transition, GetWorkflows
from .links import CreateIssueLink, CreateWebLink, GetLinkTypes, GetLinks, GetWebLinks
from .attachments import AddAttachment, GetAttachments
from .watchers import AddWatcher, GetWatchers, RemoveWatcher
from .worklogs import AddWorklog, GetWorklogs
from .projects import GetProject, GetProjects
from .components import CreateComponent, DeleteComponent, GetComponent, GetComponents
from .versions import CreateVersion, GetVersion, GetVersions, UpdateVersion
from .metadata import GetFields, GetFilter, GetFilters, GetPriorities, GetStatus, GetStatuses
from .user import GetCurrentUser, GetCurrentUserAlias, GetHealth

# All tools for registration
ALL_TOOLS = [
    # Issues
    GetIssue,
    CreateIssue,
    UpdateIssue,
    # Search
    SearchIssues,
    # Comments
    GetComments,
    AddComment,
    # Workflow
    GetTransitions,
    Transition,
    GetWorkflows,
    # Links
    GetLinks,
    GetLinkTypes,
    GetWebLinks,
    CreateIssueLink,
    CreateWebLink,
    # Attachments
    GetAttachments,
    AddAttachment,
    # Watchers
    GetWatchers,
    AddWatcher,
    RemoveWatcher,
    # Worklogs
    GetWorklogs,
    AddWorklog,
    # Projects
    GetProjects,
    GetProject,
    # Components
    GetComponents,
    GetComponent,
    CreateComponent,
    DeleteComponent,
    # Versions
    GetVersions,
    GetVersion,
    CreateVersion,
    UpdateVersion,
    # Metadata
    GetPriorities,
    GetStatuses,
    GetStatus,
    GetFields,
    GetFilters,
    GetFilter,
    # User
    GetCurrentUser,
    GetCurrentUserAlias,
    GetHealth,
]

__all__ = [
    "ALL_TOOLS",
    # Issues
    "GetIssue",
    "CreateIssue",
    "UpdateIssue",
    # Search
    "SearchIssues",
    # Comments
    "GetComments",
    "AddComment",
    # Workflow
    "GetTransitions",
    "Transition",
    "GetWorkflows",
    # Links
    "GetLinks",
    "GetLinkTypes",
    "GetWebLinks",
    "CreateIssueLink",
    "CreateWebLink",
    # Attachments
    "GetAttachments",
    "AddAttachment",
    # Watchers
    "GetWatchers",
    "AddWatcher",
    "RemoveWatcher",
    # Worklogs
    "GetWorklogs",
    "AddWorklog",
    # Projects
    "GetProjects",
    "GetProject",
    # Components
    "GetComponents",
    "GetComponent",
    "CreateComponent",
    "DeleteComponent",
    # Versions
    "GetVersions",
    "GetVersion",
    "CreateVersion",
    "UpdateVersion",
    # Metadata
    "GetPriorities",
    "GetStatuses",
    "GetStatus",
    "GetFields",
    "GetFilters",
    "GetFilter",
    # User
    "GetCurrentUser",
    "GetCurrentUserAlias",
    "GetHealth",
]
