"""Travel Agent.

旅遊規劃專家 Agent，負責處理旅遊相關的任務。
"""

from __future__ import annotations

import time

from voice_assistant.agents.base import BaseAgent
from voice_assistant.agents.state import AgentResult, AgentTask, AgentType
from voice_assistant.llm.client import LLMClient
from voice_assistant.llm.schemas import ChatMessage
from voice_assistant.tools.registry import ToolRegistry

# 旅遊建議的系統提示詞
TRAVEL_SYSTEM_PROMPT = """\
你是一個台灣旅遊專家。根據使用者的目的地和天氣資訊，提供適合的景點推薦。

回應格式：
1. 簡短總結天氣狀況
2. 推薦 2-3 個適合的景點或活動
3. 如果天氣不佳，建議室內備案

請用繁體中文回應，保持簡潔。"""


class TravelAgent(BaseAgent):
    """旅遊規劃 Agent。

    Args:
        tool_registry: Tool 註冊表
        llm_client: LLM 客戶端（用於生成建議）
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        llm_client: LLMClient,
    ) -> None:
        """初始化 Travel Agent。"""
        self._tool_registry = tool_registry
        self._llm_client = llm_client

    @property
    def agent_type(self) -> AgentType:
        """回傳 Agent 類型。"""
        return AgentType.TRAVEL

    async def execute(self, task: AgentTask) -> AgentResult:
        """執行旅遊規劃。

        支援的 task.parameters:
            - destination: str - 目的地城市（必填）
            - date: str (optional) - 出遊日期
            - include_weather: bool (optional) - 是否查詢天氣（預設 True）

        Returns:
            AgentResult with data:
                - destination: str
                - weather: dict (天氣資訊)
                - recommendations: str (景點推薦)
                - weather_suitable: bool
        """
        start_time = time.time()

        try:
            # 取得參數
            destination = task.parameters.get("destination")
            if not destination:
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=self.agent_type,
                    success=False,
                    error="缺少必要參數: destination",
                    execution_time=time.time() - start_time,
                )

            include_weather = task.parameters.get("include_weather", True)
            date = task.parameters.get("date", "")

            # 查詢天氣（如果需要）
            weather_data = None
            weather_suitable = True

            if include_weather:
                weather_result = await self._tool_registry.execute(
                    "get_weather",
                    {"city": destination, "include_details": True},
                )
                if weather_result.success:
                    weather_data = weather_result.data
                    # 判斷天氣是否適合出遊
                    weather_desc = weather_data.get("weather", "")
                    bad_weather_keywords = ["雨", "雷", "雪", "霧"]
                    weather_suitable = not any(
                        kw in weather_desc for kw in bad_weather_keywords
                    )

            # 生成旅遊建議
            recommendations = await self._generate_recommendations(
                destination, weather_data, date, weather_suitable
            )

            execution_time = time.time() - start_time

            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=True,
                data={
                    "destination": destination,
                    "weather": weather_data,
                    "recommendations": recommendations,
                    "weather_suitable": weather_suitable,
                },
                execution_time=execution_time,
            )

        except Exception as e:
            return AgentResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                success=False,
                error=f"旅遊規劃發生錯誤: {e}",
                execution_time=time.time() - start_time,
            )

    async def _generate_recommendations(
        self,
        destination: str,
        weather_data: dict | None,
        date: str,
        weather_suitable: bool,
    ) -> str:
        """生成旅遊建議。"""
        # 建構提示
        weather_info = ""
        if weather_data:
            weather_info = (
                f"天氣: {weather_data.get('weather', '未知')}, "
                f"溫度: {weather_data.get('temperature', '未知')}°C"
            )
            if "humidity" in weather_data:
                weather_info += f", 濕度: {weather_data['humidity']}%"

        date_info = f"出遊日期: {date}" if date else ""

        prompt = f"""目的地: {destination}
{weather_info}
{date_info}
天氣適合出遊: {"是" if weather_suitable else "否，請建議室內備案"}

請提供旅遊建議。"""

        messages = [ChatMessage(role="user", content=prompt)]

        response = await self._llm_client.chat(
            messages=messages,
            system_prompt=TRAVEL_SYSTEM_PROMPT,
        )

        return response.content or "抱歉，無法生成旅遊建議。"
