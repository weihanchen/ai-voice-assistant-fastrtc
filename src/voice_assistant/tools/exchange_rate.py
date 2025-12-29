"""Exchange rate query tool for voice assistant."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.schemas import ToolResult

# T002: 貨幣別名對照表（中文 → ISO 4217）
CURRENCY_ALIASES: dict[str, str] = {
    # 美元
    "美金": "USD",
    "美元": "USD",
    "美刀": "USD",
    "USD": "USD",
    # 日元
    "日幣": "JPY",
    "日圓": "JPY",
    "日元": "JPY",
    "JPY": "JPY",
    # 歐元
    "歐元": "EUR",
    "EUR": "EUR",
    # 人民幣
    "人民幣": "CNY",
    "人民币": "CNY",
    "CNY": "CNY",
    # 韓元
    "韓元": "KRW",
    "韓幣": "KRW",
    "KRW": "KRW",
    # 港幣
    "港幣": "HKD",
    "港元": "HKD",
    "HKD": "HKD",
    # 英鎊
    "英鎊": "GBP",
    "GBP": "GBP",
    # 澳幣
    "澳幣": "AUD",
    "澳元": "AUD",
    "AUD": "AUD",
    # 新台幣
    "台幣": "TWD",
    "新台幣": "TWD",
    "TWD": "TWD",
}

# T003: 貨幣顯示名稱對照表（ISO 4217 → 中文）
CURRENCY_NAMES: dict[str, str] = {
    "USD": "美元",
    "JPY": "日圓",
    "EUR": "歐元",
    "CNY": "人民幣",
    "KRW": "韓元",
    "HKD": "港幣",
    "GBP": "英鎊",
    "AUD": "澳幣",
    "TWD": "新台幣",
}

# T004: API 常數
EXCHANGE_RATE_API_BASE_URL = "https://open.er-api.com/v6/latest"
API_TIMEOUT = 10.0  # 秒


class ExchangeRateTool(BaseTool):
    """匯率查詢工具 - 查詢貨幣匯率或進行金額換算。"""

    @property
    def name(self) -> str:
        """工具名稱。"""
        return "get_exchange_rate"

    @property
    def description(self) -> str:
        """工具描述（供 LLM 判斷何時調用）。"""
        return (
            "查詢貨幣匯率或進行金額換算。"
            "支援美金、日幣、歐元、人民幣、韓元、港幣、英鎊、澳幣與新台幣。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """JSON Schema 參數定義。"""
        return {
            "type": "object",
            "properties": {
                "from_currency": {
                    "type": "string",
                    "description": "來源貨幣（中文名稱或代碼，如「美金」或「USD」）",
                },
                "to_currency": {
                    "type": "string",
                    "description": "目標貨幣（預設為新台幣 TWD）",
                    "default": "TWD",
                },
                "amount": {
                    "type": "number",
                    "description": "換算金額（預設為 1）",
                    "default": 1,
                },
            },
            "required": ["from_currency"],
        }

    def _resolve_currency(self, currency: str) -> str | None:
        """
        解析貨幣名稱為 ISO 4217 代碼。

        Args:
            currency: 使用者輸入的貨幣名稱

        Returns:
            ISO 4217 代碼，或 None 表示不支援
        """
        # 基本正規化（處理 STT 常見空白/全形空白）
        normalized_input = currency.strip().replace("\u3000", "")

        # 查詢別名對照表（先嘗試原始輸入，再嘗試大寫）
        result = CURRENCY_ALIASES.get(normalized_input)
        if result is None:
            result = CURRENCY_ALIASES.get(normalized_input.upper())
        return result

    async def _fetch_exchange_rate(self, base_code: str) -> dict[str, Any]:
        """
        從 ExchangeRate-API 取得匯率資料。

        Args:
            base_code: 基準貨幣代碼

        Returns:
            API 回應字典

        Raises:
            httpx.TimeoutException: API 逾時
            httpx.RequestError: 網路錯誤
            ValueError: API 回應錯誤
        """
        url = f"{EXCHANGE_RATE_API_BASE_URL}/{base_code}"

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()

            try:
                payload = response.json()
            except ValueError as e:
                raise ValueError("API returned non-JSON response") from e

            # 驗證回應格式
            if not isinstance(payload, dict):
                raise ValueError("API returned unexpected payload")

            if payload.get("result") != "success":
                raise ValueError("API returned error result")

            if "rates" not in payload:
                raise ValueError("API response missing rates")

            return payload

    async def execute(
        self,
        from_currency: str,
        to_currency: str = "TWD",
        amount: float = 1.0,
    ) -> ToolResult:
        """
        執行匯率查詢或換算。

        Args:
            from_currency: 來源貨幣（中文或 ISO 代碼）
            to_currency: 目標貨幣（預設 TWD）
            amount: 換算金額（預設 1.0）

        Returns:
            ToolResult: 成功時包含匯率資料，失敗時包含錯誤訊息
        """
        # 型別轉換（LLM 可能傳入字串）
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return ToolResult.fail("invalid_amount: 請提供有效的金額")

        # 驗證金額
        if amount <= 0:
            return ToolResult.fail("invalid_amount: 請提供有效的金額")

        # 解析來源貨幣
        from_code = self._resolve_currency(from_currency)
        if from_code is None:
            return ToolResult.fail(
                "unsupported_currency: "
                "目前僅支援主要國際貨幣，例如美金、日幣、歐元、人民幣等"
            )

        # 解析目標貨幣
        to_code = self._resolve_currency(to_currency)
        if to_code is None:
            return ToolResult.fail(
                "unsupported_currency: "
                "目前僅支援主要國際貨幣，例如美金、日幣、歐元、人民幣等"
            )

        # 檢查是否為相同貨幣
        if from_code == to_code:
            return ToolResult.fail("same_currency: 您查詢的是相同貨幣，無需換算")

        try:
            # 呼叫 API（使用 from_code 作為基準貨幣）
            data = await self._fetch_exchange_rate(from_code)
            rates = data.get("rates", {})

            # 驗證 rates 是字典
            if not isinstance(rates, dict):
                return ToolResult.fail("api_error: 無法取得匯率資訊，請稍後再試")

            # 取得匯率
            rate = rates.get(to_code)
            if rate is None:
                return ToolResult.fail("api_error: 無法取得匯率資訊，請稍後再試")

            # 驗證 rate 是數值類型
            if not isinstance(rate, int | float):
                return ToolResult.fail("api_error: 無法取得匯率資訊，請稍後再試")

            # 計算換算結果
            converted_amount = amount * rate

            result: dict[str, Any] = {
                "from_currency": from_code,
                "from_amount": amount,
                "to_currency": to_code,
                "to_amount": round(converted_amount, 2),
                "rate": rate,
                "queried_at": datetime.now(UTC).isoformat(),
            }

            return ToolResult.ok(result)

        except httpx.TimeoutException:
            return ToolResult.fail("api_timeout: 匯率服務暫時無法使用，請稍後再試")
        except httpx.HTTPStatusError:
            return ToolResult.fail("api_error: 匯率服務暫時無法使用，請稍後再試")
        except httpx.RequestError:
            return ToolResult.fail("network_error: 網路連線異常，請檢查網路狀態")
        except ValueError:
            return ToolResult.fail("api_error: 無法取得匯率資訊，請稍後再試")
