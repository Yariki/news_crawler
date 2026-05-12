from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    TEAM_LEAD = "team_lead"
    TEAM_MEMBER = "team_member"
    TEAM_VIEWER = "team_viewer"
    SUPER_VIEWER = "super_viewer"


class Permission(StrEnum):
    SOURCE_CREATE = "source:create"
    SOURCE_READ = "source:read"
    SOURCE_UPDATE = "source:update"
    SOURCE_DELETE = "source:delete"
    JOB_RUN = "job:run"
    KEYWORD_CREATE = "keyword:create"
    KEYWORD_READ = "keyword:read"
    KEYWORD_UPDATE = "keyword:update"
    KEYWORD_DELETE = "keyword:delete"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_READ = "user:read"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),
    Role.TEAM_LEAD: {
        Permission.SOURCE_CREATE,
        Permission.SOURCE_READ,
        Permission.SOURCE_UPDATE,
        Permission.SOURCE_DELETE,
        Permission.JOB_RUN,
        Permission.KEYWORD_CREATE,
        Permission.KEYWORD_READ,
        Permission.KEYWORD_UPDATE,
        Permission.KEYWORD_DELETE,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_READ,
    },
    Role.TEAM_MEMBER: {
        Permission.SOURCE_CREATE,
        Permission.SOURCE_READ,
        Permission.KEYWORD_CREATE,
        Permission.KEYWORD_READ,
    },
    Role.TEAM_VIEWER: {
        Permission.SOURCE_READ,
        Permission.KEYWORD_READ,
        Permission.USER_READ,
    },
    Role.SUPER_VIEWER: {
        Permission.SOURCE_READ,
        Permission.KEYWORD_READ,
        Permission.USER_READ,
    },
}

