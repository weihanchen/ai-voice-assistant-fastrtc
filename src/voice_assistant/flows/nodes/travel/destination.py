"""目的地解析節點。

從使用者輸入中提取並驗證目的地城市。
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from voice_assistant.flows.state import FlowState, TravelPlanState
from voice_assistant.tools.weather import TAIWAN_CITIES

if TYPE_CHECKING:
    from voice_assistant.llm.client import LLMClient


DESTINATION_EXTRACT_PROMPT = """你是一個旅遊助手。請從使用者的輸入中提取目的地城市名稱。

支援的台灣城市：台北、新北、桃園、台中、台南、高雄、基隆、新竹、嘉義、屏東、宜蘭、花蓮、台東

請以 JSON 格式回覆，包含以下欄位：
- destination: 提取的城市名稱（如果無法識別則為 null）

範例：
使用者：我想去台北玩
回覆：{"destination": "台北"}

使用者：想去高雄旅遊
回覆：{"destination": "高雄"}

使用者：幫我規劃行程
回覆：{"destination": null}
"""


def create_destination_parser_node(llm_client: LLMClient) -> Any:
    """建立目的地解析節點。

    Args:
        llm_client: LLM 客戶端

    Returns:
        可用於 LangGraph 的節點函式
    """
    from voice_assistant.llm.schemas import ChatMessage

    async def parse_destination(state: FlowState) -> dict[str, Any]:
        """解析目的地節點函式。

        Args:
            state: 流程狀態

        Returns:
            更新的狀態欄位
        """
        user_input = state.get("user_input", "")

        try:
            response = await llm_client.chat(
                messages=[ChatMessage(role="user", content=user_input)],
                system_prompt=DESTINATION_EXTRACT_PROMPT,
            )

            # 解析 JSON 回應
            content = response.content or "{}"
            # 移除可能的 markdown 程式碼區塊標記
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])

            result = json.loads(content)
            destination = result.get("destination")

            # 驗證城市
            if destination and destination in TAIWAN_CITIES:
                travel_state: TravelPlanState = {
                    "destination": destination,
                    "destination_valid": True,
                }
            elif destination:
                # 城市不在支援列表中
                travel_state = {
                    "destination": destination,
                    "destination_valid": False,
                }
            else:
                # 無法識別目的地
                travel_state = {
                    "destination": None,
                    "destination_valid": False,
                }

            return {"travel_state": travel_state}

        except (json.JSONDecodeError, KeyError):
            # LLM 回應無法解析
            return {
                "travel_state": {
                    "destination": None,
                    "destination_valid": False,
                },
                "error": "無法識別目的地，請指定您想去的城市",
            }
        except Exception as e:
            return {
                "travel_state": {
                    "destination": None,
                    "destination_valid": False,
                },
                "error": f"處理目的地時發生錯誤: {e!s}",
            }

    return parse_destination
