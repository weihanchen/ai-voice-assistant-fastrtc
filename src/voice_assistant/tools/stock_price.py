"""Stock price query tool for voice assistant."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from voice_assistant.tools.base import BaseTool
from voice_assistant.tools.schemas import ToolResult

# T002: 台股對照表（台灣 50 成分股）
TW_STOCK_ALIASES: dict[str, str] = {
    # 中文名稱 → 完整代碼
    "台積電": "2330.TW",
    "鴻海": "2317.TW",
    "聯發科": "2454.TW",
    "台達電": "2308.TW",
    "中華電": "2412.TW",
    "富邦金": "2881.TW",
    "國泰金": "2882.TW",
    "中信金": "2891.TW",
    "台塑": "1301.TW",
    "南亞": "1303.TW",
    "台化": "1326.TW",
    "中鋼": "2002.TW",
    "統一": "1216.TW",
    "台泥": "1101.TW",
    "亞泥": "1102.TW",
    "廣達": "2382.TW",
    "和碩": "4938.TW",
    "仁寶": "2324.TW",
    "華碩": "2357.TW",
    "宏碁": "2353.TW",
    "緯創": "3231.TW",
    "大立光": "3008.TW",
    "玉山金": "2884.TW",
    "元大金": "2885.TW",
    "兆豐金": "2886.TW",
    "第一金": "2892.TW",
    "華南金": "2880.TW",
    "台新金": "2887.TW",
    "永豐金": "2890.TW",
    "日月光投控": "3711.TW",
    "聯電": "2303.TW",
    "瑞昱": "2379.TW",
    "聯詠": "3034.TW",
    "矽力": "6415.TW",
    "台灣大": "3045.TW",
    "遠傳": "4904.TW",
    "長榮": "2603.TW",
    "陽明": "2609.TW",
    "萬海": "2615.TW",
    "長榮航": "2618.TW",
    "華航": "2610.TW",
    "台塑化": "6505.TW",
    "正新": "2105.TW",
    "研華": "2395.TW",
    "可成": "2474.TW",
    "台光電": "2383.TW",
    "穩懋": "3105.TW",
    "群創": "3481.TW",
    "友達": "2409.TW",
    "欣興": "3037.TW",
    # 純數字代碼 → 完整代碼
    "2330": "2330.TW",
    "2317": "2317.TW",
    "2454": "2454.TW",
    "2308": "2308.TW",
    "2412": "2412.TW",
    "2881": "2881.TW",
    "2882": "2882.TW",
    "2891": "2891.TW",
    "1301": "1301.TW",
    "1303": "1303.TW",
    "1326": "1326.TW",
    "2002": "2002.TW",
    "1216": "1216.TW",
    "1101": "1101.TW",
    "1102": "1102.TW",
    "2382": "2382.TW",
    "4938": "4938.TW",
    "2324": "2324.TW",
    "2357": "2357.TW",
    "2353": "2353.TW",
    "3231": "3231.TW",
    "3008": "3008.TW",
    "2884": "2884.TW",
    "2885": "2885.TW",
    "2886": "2886.TW",
    "2892": "2892.TW",
    "2880": "2880.TW",
    "2887": "2887.TW",
    "2890": "2890.TW",
    "3711": "3711.TW",
    "2303": "2303.TW",
    "2379": "2379.TW",
    "3034": "3034.TW",
    "6415": "6415.TW",
    "3045": "3045.TW",
    "4904": "4904.TW",
    "2603": "2603.TW",
    "2609": "2609.TW",
    "2615": "2615.TW",
    "2618": "2618.TW",
    "2610": "2610.TW",
    "6505": "6505.TW",
    "2105": "2105.TW",
    "2395": "2395.TW",
    "2474": "2474.TW",
    "2383": "2383.TW",
    "3105": "3105.TW",
    "3481": "3481.TW",
    "2409": "2409.TW",
    "3037": "3037.TW",
}

# T003: 美股對照表（S&P 500 前 30 大市值）
US_STOCK_ALIASES: dict[str, str] = {
    # 中文名稱 → 代碼
    "蘋果": "AAPL",
    "微軟": "MSFT",
    "輝達": "NVDA",
    "亞馬遜": "AMZN",
    "谷歌": "GOOGL",
    "Google": "GOOGL",
    "Meta": "META",
    "臉書": "META",
    "特斯拉": "TSLA",
    "波克夏": "BRK-B",
    "聯合健康": "UNH",
    "嬌生": "JNJ",
    "摩根大通": "JPM",
    "Visa": "V",
    "寶僑": "PG",
    "萬事達卡": "MA",
    "好市多": "COST",
    "埃森哲": "ACN",
    "雪佛龍": "CVX",
    "艾乐美": "LLY",
    "禮來": "LLY",
    "家得寶": "HD",
    "輝瑞": "PFE",
    "百事": "PEP",
    "可口可樂": "KO",
    "博通": "AVGO",
    "迪士尼": "DIS",
    "思科": "CSCO",
    "Adobe": "ADBE",
    "網飛": "NFLX",
    "Netflix": "NFLX",
    "超微": "AMD",
    "英特爾": "INTC",
    "高通": "QCOM",
    # 英文名稱 → 代碼
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Nvidia": "NVDA",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Tesla": "TSLA",
    "Berkshire": "BRK-B",
    "UnitedHealth": "UNH",
    "Johnson": "JNJ",
    "JPMorgan": "JPM",
    "Procter": "PG",
    "Mastercard": "MA",
    "Costco": "COST",
    "Accenture": "ACN",
    "Chevron": "CVX",
    "Eli Lilly": "LLY",
    "Home Depot": "HD",
    "Pfizer": "PFE",
    "Pepsi": "PEP",
    "PepsiCo": "PEP",
    "Coca-Cola": "KO",
    "Broadcom": "AVGO",
    "Disney": "DIS",
    "Cisco": "CSCO",
    "Intel": "INTC",
    "Qualcomm": "QCOM",
    # 代碼本身（大寫）
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "NVDA": "NVDA",
    "AMZN": "AMZN",
    "GOOGL": "GOOGL",
    "GOOG": "GOOGL",
    "META": "META",
    "TSLA": "TSLA",
    "BRK-B": "BRK-B",
    "UNH": "UNH",
    "JNJ": "JNJ",
    "JPM": "JPM",
    "V": "V",
    "PG": "PG",
    "MA": "MA",
    "COST": "COST",
    "ACN": "ACN",
    "CVX": "CVX",
    "LLY": "LLY",
    "HD": "HD",
    "PFE": "PFE",
    "PEP": "PEP",
    "KO": "KO",
    "AVGO": "AVGO",
    "DIS": "DIS",
    "CSCO": "CSCO",
    "ADBE": "ADBE",
    "NFLX": "NFLX",
    "AMD": "AMD",
    "INTC": "INTC",
    "QCOM": "QCOM",
}

# T004: 股票顯示名稱對照表（代碼 → 中文）
STOCK_DISPLAY_NAMES: dict[str, str] = {
    # 台股
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "2454.TW": "聯發科",
    "2308.TW": "台達電",
    "2412.TW": "中華電",
    "2881.TW": "富邦金",
    "2882.TW": "國泰金",
    "2891.TW": "中信金",
    "1301.TW": "台塑",
    "1303.TW": "南亞",
    "1326.TW": "台化",
    "2002.TW": "中鋼",
    "1216.TW": "統一",
    "1101.TW": "台泥",
    "1102.TW": "亞泥",
    "2382.TW": "廣達",
    "4938.TW": "和碩",
    "2324.TW": "仁寶",
    "2357.TW": "華碩",
    "2353.TW": "宏碁",
    "3231.TW": "緯創",
    "3008.TW": "大立光",
    "2884.TW": "玉山金",
    "2885.TW": "元大金",
    "2886.TW": "兆豐金",
    "2892.TW": "第一金",
    "2880.TW": "華南金",
    "2887.TW": "台新金",
    "2890.TW": "永豐金",
    "3711.TW": "日月光投控",
    "2303.TW": "聯電",
    "2379.TW": "瑞昱",
    "3034.TW": "聯詠",
    "6415.TW": "矽力",
    "3045.TW": "台灣大",
    "4904.TW": "遠傳",
    "2603.TW": "長榮",
    "2609.TW": "陽明",
    "2615.TW": "萬海",
    "2618.TW": "長榮航",
    "2610.TW": "華航",
    "6505.TW": "台塑化",
    "2105.TW": "正新",
    "2395.TW": "研華",
    "2474.TW": "可成",
    "2383.TW": "台光電",
    "3105.TW": "穩懋",
    "3481.TW": "群創",
    "2409.TW": "友達",
    "3037.TW": "欣興",
    # 美股
    "AAPL": "蘋果",
    "MSFT": "微軟",
    "NVDA": "輝達",
    "AMZN": "亞馬遜",
    "GOOGL": "谷歌",
    "META": "Meta",
    "TSLA": "特斯拉",
    "BRK-B": "波克夏",
    "UNH": "聯合健康",
    "JNJ": "嬌生",
    "JPM": "摩根大通",
    "V": "Visa",
    "PG": "寶僑",
    "MA": "萬事達卡",
    "COST": "好市多",
    "ACN": "埃森哲",
    "CVX": "雪佛龍",
    "LLY": "禮來",
    "HD": "家得寶",
    "PFE": "輝瑞",
    "PEP": "百事",
    "KO": "可口可樂",
    "AVGO": "博通",
    "DIS": "迪士尼",
    "CSCO": "思科",
    "ADBE": "Adobe",
    "NFLX": "網飛",
    "AMD": "超微",
    "INTC": "英特爾",
    "QCOM": "高通",
}

# API 常數
API_TIMEOUT = 8.0  # 秒


class StockPriceTool(BaseTool):
    """股票報價查詢工具 - 查詢台股與美股的即時報價。"""

    @property
    def name(self) -> str:
        """工具名稱。"""
        return "get_stock_price"

    @property
    def description(self) -> str:
        """工具描述（供 LLM 判斷何時調用）。"""
        return (
            "查詢股票即時報價。"
            "支援台股（台灣 50 成分股）與美股（S&P 500 前 30 大市值股票）。"
            "可使用中文名稱（如「台積電」、「蘋果」）、"
            "英文名稱（如「Apple」）或股票代碼（如「2330」、「AAPL」）查詢。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """JSON Schema 參數定義。"""
        return {
            "type": "object",
            "properties": {
                "stock": {
                    "type": "string",
                    "description": (
                        "要查詢的股票名稱或代碼，例如：台積電、Apple、2330、AAPL"
                    ),
                },
            },
            "required": ["stock"],
        }

    def _resolve_stock(self, stock: str) -> tuple[str, str] | None:
        """
        解析股票名稱為代碼與市場。

        Args:
            stock: 使用者輸入的股票名稱或代碼

        Returns:
            (symbol, market) 元組，或 None 表示不支援
        """
        # 型別檢查（防止 LLM 傳入非字串）
        if not isinstance(stock, str):
            return None

        # 基本正規化（處理 STT 常見空白/全形空白）
        normalized = stock.strip().replace("\u3000", "").replace(" ", "")

        # 先查台股對照表
        if normalized in TW_STOCK_ALIASES:
            symbol = TW_STOCK_ALIASES[normalized]
            return (symbol, "TW")

        # 再查美股對照表（大小寫不敏感）
        upper = normalized.upper()
        if upper in US_STOCK_ALIASES:
            symbol = US_STOCK_ALIASES[upper]
            return (symbol, "US")
        if normalized in US_STOCK_ALIASES:
            symbol = US_STOCK_ALIASES[normalized]
            return (symbol, "US")

        return None

    async def _fetch_price(self, symbol: str) -> dict[str, Any]:
        """
        從 yfinance 取得股價資料。

        Args:
            symbol: 股票代碼

        Returns:
            包含 price 和 currency 的字典

        Raises:
            asyncio.TimeoutError: API 逾時
            Exception: 其他 API 錯誤
        """

        def _sync_fetch() -> dict[str, Any]:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            return {
                "price": info.last_price,
                "currency": getattr(info, "currency", None),
            }

        return await asyncio.wait_for(
            asyncio.to_thread(_sync_fetch),
            timeout=API_TIMEOUT,
        )

    async def execute(self, stock: str) -> ToolResult:
        """
        執行股價查詢。

        Args:
            stock: 股票名稱或代碼

        Returns:
            ToolResult: 成功時包含股價資料，失敗時包含錯誤訊息
        """
        # 解析股票
        resolved = self._resolve_stock(stock)
        if not resolved:
            return ToolResult.fail(
                "unsupported_stock: 抱歉，找不到這支股票，請確認名稱或代碼是否正確"
            )

        symbol, market = resolved
        display_name = STOCK_DISPLAY_NAMES.get(symbol, symbol)

        try:
            # 呼叫 API
            data = await self._fetch_price(symbol)
            price = data.get("price")
            currency = data.get("currency")

            # 驗證必要欄位
            if price is None:
                return ToolResult.fail(
                    "no_data: 無法取得報價資訊，該股票可能已下市或暫停交易"
                )

            # 驗證 price 是數值類型（排除 bool）
            if isinstance(price, bool) or not isinstance(price, int | float):
                return ToolResult.fail(
                    "no_data: 無法取得報價資訊，該股票可能已下市或暫停交易"
                )

            # 組裝結果
            result: dict[str, Any] = {
                "symbol": symbol,
                "name": display_name,
                "price": round(price, 2),
                "currency": currency or ("TWD" if market == "TW" else "USD"),
                "market": market,
                "queried_at": datetime.now(UTC).isoformat(),
            }

            return ToolResult.ok(result)

        except TimeoutError:
            return ToolResult.fail("api_timeout: 股票查詢逾時，請稍後再試")
        except Exception:
            return ToolResult.fail("api_error: 股票服務暫時無法使用，請稍後再試")
