"""
預設角色基底類別，供所有預設腳色繼承。
"""

from ..base import BaseRole
from ..schemas import Role


class BasePredefinedRole(Role, BaseRole):
    """
    預設角色抽象類別，所有預設腳色繼承此類。
    共用欄位：系統提示詞、語氣、描述、啟用狀態、範例回應等。
    """

    # 繼承自 schemas.Role，僅需定義必要方法與可選欄位

    def get_system_prompt(self) -> str:
        """
        回傳該角色的 LLM 系統提示語（繁體中文）。
        """
        return self.system_prompt
