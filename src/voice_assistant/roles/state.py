"""
角色狀態管理器。歷史切換記錄與當前狀態。
"""

from datetime import datetime

from pydantic import BaseModel, Field

from .log import logger


class RoleTransition(BaseModel):
    """
    角色切換記錄
    """

    from_role: str | None = Field(None, description="來源角色 ID")
    to_role: str = Field(..., description="目標角色 ID")
    reason: str = Field(..., description="切換原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="切換時間")


class RoleState(BaseModel):
    """
    角色狀態管理器
    """

    current_role_id: str | None = Field(None, description="當前角色 ID")
    transition_history: list[RoleTransition] = Field(
        default_factory=list, description="切換歷史"
    )
    session_id: str = Field(..., description="對話會話 ID")
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="最近更新時間"
    )

    def add_transition(self, from_role: str | None, to_role: str, reason: str):
        """
        增加一筆切換記錄並更新狀態。
        """
        self.transition_history.append(
            RoleTransition(from_role=from_role, to_role=to_role, reason=reason)
        )
        self.current_role_id = to_role
        self.last_updated = datetime.now()
        logger.info(f"角色切換: {from_role} → {to_role}, 原因: {reason}")

    def switch_role(self, to_role_id: str | None, reason: str = "手動切換") -> bool:
        """
        切換角色並記錄歷史，若重複、None 或無效 id 則降級並回傳 False。
        Args:
            to_role_id: 目標角色 ID（可為 None）
            reason: 切換原因
        Returns:
            bool: 切換成功為 True，失敗/降級回傳 False
        """
        if to_role_id is None or to_role_id == "":
            logger.warning("切換角色失敗：目標角色 ID 為 None 或空字串，已降級。")
            return False
        from_role = self.current_role_id
        if from_role == to_role_id:
            logger.warning(f"當前角色已經是 {to_role_id}，忽略切換。")
            return False
        self.add_transition(from_role, to_role_id, reason)
        return True
