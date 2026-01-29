"""
角色系統例外類別定義。
"""


class RoleRegistryError(Exception):
    """角色註冊相關錯誤"""

    pass


class RoleNotFoundError(Exception):
    """找不到指定角色時拋出的例外"""

    pass


class RoleSwitchError(Exception):
    """角色切換失敗時拋出的例外"""

    pass
