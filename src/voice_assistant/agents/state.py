"""Multi-Agent State Models.

定義多代理協作系統的資料結構，包含任務、結果、狀態等核心實體。
"""

from __future__ import annotations

import operator
from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from typing_extensions import TypedDict


class AgentType(str, Enum):
    """Agent 類型識別碼。

    用於 Supervisor 分派任務時識別目標 Agent。
    """

    WEATHER = "weather"
    FINANCE = "finance"
    TRAVEL = "travel"
    GENERAL = "general"


class AgentTask(BaseModel):
    """Agent 任務。

    代表 Supervisor 分派給專家 Agent 的單一任務。

    Attributes:
        task_id: 任務唯一識別碼（UUID）
        agent_type: 目標 Agent 類型
        description: 任務描述（自然語言）
        parameters: 任務參數（如城市名、股票代碼）
        created_at: 建立時間
    """

    task_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_type: AgentType
    description: str = Field(min_length=1)
    parameters: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class AgentResult(BaseModel):
    """Agent 執行結果。

    代表專家 Agent 的執行結果，包含成功/失敗狀態與回傳資料。

    Attributes:
        task_id: 對應的任務識別碼
        agent_type: 執行的 Agent 類型
        success: 執行是否成功
        data: 成功時的結果資料
        error: 失敗時的錯誤訊息
        execution_time: 執行耗時（秒）
    """

    task_id: str
    agent_type: AgentType
    success: bool
    data: dict | None = None
    error: str | None = None
    execution_time: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_result(self) -> AgentResult:
        """驗證結果完整性。"""
        if self.success and self.data is None:
            raise ValueError("成功結果必須包含 data")
        if not self.success and self.error is None:
            raise ValueError("失敗結果必須包含 error")
        return self


class TaskDecomposition(BaseModel):
    """任務拆解結果。

    Supervisor 分析使用者輸入後產生的任務清單。

    Attributes:
        tasks: 拆解出的任務清單
        reasoning: 拆解理由（debug 用）
        requires_aggregation: 是否需要彙整多個結果
    """

    tasks: list[AgentTask] = Field(min_length=1)
    reasoning: str
    requires_aggregation: bool = False

    @model_validator(mode="after")
    def validate_aggregation(self) -> TaskDecomposition:
        """若任務數大於 1，自動設定需要彙整。"""
        if len(self.tasks) > 1:
            self.requires_aggregation = True
        return self


class MultiAgentState(TypedDict, total=False):
    """多代理流程狀態。

    LangGraph 流程的完整狀態，用於追蹤執行進度。

    Attributes:
        user_input: 使用者原始輸入
        decomposition: 任務拆解結果
        pending_tasks: 待執行的任務
        results: 已完成的結果（使用 append reducer）
        final_response: 最終回應
        error: 流程錯誤訊息
    """

    # 輸入
    user_input: str

    # Supervisor 輸出
    decomposition: TaskDecomposition | None

    # 執行追蹤
    pending_tasks: list[AgentTask]
    results: Annotated[list[AgentResult], operator.add]  # append reducer

    # 輸出
    final_response: str
    error: str | None
