"""
Intent 資料模型骨架（細節待補）。
"""

from pydantic import BaseModel, Field


class Intent(BaseModel):
    """用戶意圖資料模型"""

    name: str = Field(..., description="意圖名稱")
    description: str | None = Field(None, description="說明")
    params: dict = Field(
        default_factory=dict, description="參數字典，可攜帶目標角色 id、score 等"
    )
    score: float | None = Field(None, description="LLM 信心分數")
