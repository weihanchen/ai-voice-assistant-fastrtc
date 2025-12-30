"""Tools module for voice assistant."""

from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.exchange_rate import ExchangeRateTool
from voice_assistant.tools.registry import ToolRegistry
from voice_assistant.tools.schemas import ToolResult
from voice_assistant.tools.stock_price import StockPriceTool
from voice_assistant.tools.weather import WeatherTool

__all__ = [
    "BaseTool",
    "ExchangeRateTool",
    "StockPriceTool",
    "ToolRegistry",
    "ToolResult",
    "WeatherTool",
]
