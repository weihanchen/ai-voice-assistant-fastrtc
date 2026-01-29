"""
角色與相關資料模型。根據 data-model.md。
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoleType(str, Enum):
    INTERVIEWER = "interviewer"  # 面試官
    ASSISTANT = "assistant"  # 助理
    COACH = "coach"  # 教練
    CUSTOM = "custom"  # 自訂


class Role(BaseModel):
    """AI 角色定義"""

    # 基本屬性
    id: str = Field(..., description="角色唯一識別碼")
    name: str = Field(..., description="角色顯示名稱")
    role_type: RoleType = Field(..., description="角色類型")
    # 行為定義
    system_prompt: str = Field(..., description="LLM 系統提示語")
    tone_style: str = Field(..., description="語氣風格描述")
    # 元資料
    description: str | None = Field(None, description="角色描述")
    example_responses: list[str] = Field(default_factory=list, description="範例回應")
    # 配置
    is_active: bool = Field(True, description="是否啟用")
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    updated_at: datetime | None = Field(None, description="更新時間")

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("system_prompt")
    def validate_system_prompt(cls, v):
        if not v.strip():
            raise ValueError("系統提示語不能為空")
        return v.strip()

    @field_validator("id")
    def validate_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("角色 ID 不能為空")
        return v.strip().lower()
