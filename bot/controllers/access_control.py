from enum import Enum

class Role(Enum):
    ADMIN = "admin"
    FREE = "free"
    PREMIUM = "premium"

class Permissions(Enum):
    USE_FREE_FEATURE = "use_free_feature"
    USE_PREMIUM_FEATURE = "use_premium_feature"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permissions.USE_FREE_FEATURE, Permissions.USE_PREMIUM_FEATURE],
    Role.FREE: [Permissions.USE_FREE_FEATURE],
    Role.PREMIUM: [Permissions.USE_FREE_FEATURE, Permissions.USE_PREMIUM_FEATURE],
}

def user_has_permission(user, permission):
    role = Role(user.role)
    permissions = ROLE_PERMISSIONS[role]
    return permission in permissions
