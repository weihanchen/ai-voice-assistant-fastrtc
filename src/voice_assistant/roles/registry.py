"""
角色註冊與查詢系統。
"""

from .exceptions import RoleRegistryError
from .log import logger
from .schemas import Role


class RoleRegistry:
    """
    角色註冊表，可註冊、查詢、移除、重設角色，並確保唯一。
    """

    def __init__(self):
        self._roles: dict[str, Role] = {}

    def register(self, role: Role):
        """
        註冊新角色，若 id 已存在則拋出錯誤。
        """
        if role.id in self._roles:
            raise RoleRegistryError(f"角色 ID 已存在: {role.id}")
        self._roles[role.id] = role
        logger.info(f"註冊角色: {role.id} → {role.name}")

    def get(self, role_id: str) -> Role:
        """
        查詢角色，不存在則拋例外。
        """
        try:
            return self._roles[role_id]
        except KeyError:
            logger.error(f"查無角色: {role_id}")
            raise RoleRegistryError(f"查無角色: {role_id}")

    def get_id_by_name(self, name: str) -> str | None:
        """
        透過角色名稱取得其 id，若沒有對應則回傳 None。
        """
        for role in self._roles.values():
            if role.name == name:
                return role.id
        return None

    def remove(self, role_id: str):
        """
        移除指定角色，不存在則拋例外。
        """
        if role_id in self._roles:
            del self._roles[role_id]
            logger.info(f"移除角色: {role_id}")
        else:
            logger.error(f"查無角色: {role_id}")
            raise RoleRegistryError(f"查無角色: {role_id}")

    def reset(self):
        """重設所有註冊角色（多用於測試）"""
        self._roles.clear()
        logger.info("角色註冊表已重設")

    def list_roles(self) -> list[Role]:
        """
        列出所有已註冊角色。
        """
        return list(self._roles.values())
