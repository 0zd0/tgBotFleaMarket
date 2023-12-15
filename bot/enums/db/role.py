from enum import Enum


class Role(str, Enum):
    BLOCKED = "blocked"
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


ADMINS = [Role.MANAGER, Role.ADMIN, Role.SUPER_ADMIN]
ALL = [Role.USER, Role.MANAGER, Role.ADMIN, Role.SUPER_ADMIN]
