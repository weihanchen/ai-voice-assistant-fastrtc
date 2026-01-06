"""測試 LangGraph 流程執行器。"""

import asyncio

from dotenv import load_dotenv

from voice_assistant.config import get_settings
from voice_assistant.flows import FlowExecutor
from voice_assistant.llm import LLMClient
from voice_assistant.tools import ExchangeRateTool, StockPriceTool, WeatherTool
from voice_assistant.tools.registry import ToolRegistry

# 載入環境變數
load_dotenv()


async def test_flow() -> None:
    """測試流程執行。"""
    settings = get_settings()

    # 建立 LLM Client
    llm = LLMClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )

    # 建立 Tool Registry 並註冊工具
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(ExchangeRateTool())
    registry.register(StockPriceTool())

    executor = FlowExecutor(llm, registry)

    # 測試旅遊規劃
    print("=" * 50)
    print("測試: 我想去台北玩")
    print("=" * 50)
    result = await executor.execute("我想去台北玩")
    print(f"回應: {result}")
    print()

    # 測試天氣查詢
    print("=" * 50)
    print("測試: 高雄天氣如何")
    print("=" * 50)
    result = await executor.execute("高雄天氣如何")
    print(f"回應: {result}")
    print()

    # 取得流程圖
    print("=" * 50)
    print("Mermaid 流程圖:")
    print("=" * 50)
    print(executor.get_visualization())


if __name__ == "__main__":
    asyncio.run(test_flow())
