from enum import StrEnum


class Resources(StrEnum):
    SOURCE = "source"
    ARTICLE = "article"
    ALERT = "alert"
    JOB = "job"
    KEYWORD = "keyword"
    DASHBOARD = "dashboard"

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_


class Actions(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    RUN = "run"

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_


class ScopeMode(StrEnum):
    ALL = "*"
    ANY = "any"
    OWN = "own"

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_
