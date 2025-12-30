# Data Model: Stock Price Query

**Feature**: 004-stock-price-query
**Date**: 2025-12-29

## 概述

股票報價查詢功能的資料模型，定義查詢輸入、回應輸出及內部對照表結構。

---

## 1. 核心實體

### 1.1 StockQuery（查詢輸入）

使用者的股票查詢請求，由 LLM Function Calling 解析。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `stock` | `string` | ✅ | 股票名稱或代碼（中文、英文或代碼） |

**範例輸入**：
- 「台積電」
- 「Apple」
- 「2330」
- 「AAPL」

### 1.2 StockQuote（報價結果）

成功查詢時回傳的股票報價資料。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `symbol` | `string` | 股票代碼（如 2330.TW, AAPL） |
| `name` | `string` | 股票中文名稱（如 台積電, 蘋果） |
| `price` | `float` | 當前股價 |
| `currency` | `string` | 貨幣單位（TWD, USD） |
| `market` | `string` | 所屬市場（TW, US） |
| `queried_at` | `string` | 查詢時間（ISO 8601 格式） |

**JSON 範例**：

```json
{
  "symbol": "2330.TW",
  "name": "台積電",
  "price": 1080.0,
  "currency": "TWD",
  "market": "TW",
  "queried_at": "2025-12-29T10:30:00+00:00"
}
```

### 1.3 ToolResult（工具回傳）

繼承自 `voice_assistant.tools.schemas.ToolResult`，包裝成功或失敗結果。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `data` | `dict \| None` | 成功時為 StockQuote，失敗時為 None |
| `error` | `str \| None` | 失敗時的錯誤訊息 |

---

## 2. 對照表結構

### 2.1 台股對照表 (TW_STOCK_ALIASES)

將中文名稱與代碼對應到完整的 Yahoo Finance 股票代碼。

```python
TW_STOCK_ALIASES: dict[str, str] = {
    # 中文名稱 → 完整代碼
    "台積電": "2330.TW",
    "鴻海": "2317.TW",
    "聯發科": "2454.TW",
    "中華電": "2412.TW",
    "台達電": "2308.TW",
    # ... (台灣 50 成分股)

    # 純數字代碼 → 完整代碼
    "2330": "2330.TW",
    "2317": "2317.TW",
    # ...
}
```

### 2.2 美股對照表 (US_STOCK_ALIASES)

將中文名稱、英文名稱與代碼對應到股票代碼。

```python
US_STOCK_ALIASES: dict[str, str] = {
    # 中文名稱 → 代碼
    "蘋果": "AAPL",
    "微軟": "MSFT",
    "亞馬遜": "AMZN",
    "谷歌": "GOOGL",
    "特斯拉": "TSLA",
    "輝達": "NVDA",
    # ... (S&P 500 前 30 大)

    # 英文名稱 → 代碼
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    # ...

    # 代碼本身
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    # ...
}
```

### 2.3 顯示名稱對照表 (STOCK_DISPLAY_NAMES)

供回應時顯示中文名稱。

```python
STOCK_DISPLAY_NAMES: dict[str, str] = {
    # 台股
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    # 美股
    "AAPL": "蘋果",
    "MSFT": "微軟",
    # ...
}
```

---

## 3. 錯誤類型

| 錯誤代碼 | 說明 | 使用者訊息 |
|----------|------|-----------|
| `unsupported_stock` | 股票不在對照表中 | 抱歉，找不到這支股票，請確認名稱或代碼是否正確 |
| `api_error` | yfinance API 錯誤 | 股票服務暫時無法使用，請稍後再試 |
| `no_data` | API 回傳無報價資料 | 無法取得報價資訊，該股票可能已下市或暫停交易 |
| `network_error` | 網路連線失敗 | 網路連線異常，請檢查網路狀態 |
| `api_timeout` | API 逾時 | 股票查詢逾時，請稍後再試 |

---

## 4. 狀態流程

```
使用者語音輸入
      ↓
[ASR 轉文字]
      ↓
[LLM 意圖識別] → 呼叫 get_stock_price(stock="台積電")
      ↓
[StockPriceTool.execute]
      ↓
  ┌───────────────────────────────────────┐
  │ 1. 正規化輸入                          │
  │ 2. 查詢 TW_STOCK_ALIASES              │
  │    └─ 找到 → symbol = "2330.TW"       │
  │    └─ 沒找到 → 查詢 US_STOCK_ALIASES  │
  │         └─ 找到 → symbol              │
  │         └─ 沒找到 → 回傳錯誤           │
  │ 3. 呼叫 yfinance API                  │
  │ 4. 驗證回傳資料                        │
  │ 5. 組裝 StockQuote                     │
  └───────────────────────────────────────┘
      ↓
[ToolResult.ok(StockQuote)] 或 [ToolResult.fail(error)]
      ↓
[LLM 生成自然語言回應]
      ↓
[TTS 語音輸出]
```
