# Contract: StockPriceTool

**Feature**: 004-stock-price-query
**Date**: 2025-12-29

## 概述

股票報價查詢工具的 API 合約，定義 OpenAI Function Calling 介面與回應格式。

---

## 1. Function Calling 定義

### 1.1 工具名稱

```
get_stock_price
```

### 1.2 工具描述

```
查詢股票即時報價。支援台股（台灣 50 成分股）與美股（S&P 500 前 30 大市值股票）。
可使用中文名稱（如「台積電」、「蘋果」）、英文名稱（如「Apple」）或股票代碼（如「2330」、「AAPL」）查詢。
```

### 1.3 參數定義（JSON Schema）

```json
{
  "type": "object",
  "properties": {
    "stock": {
      "type": "string",
      "description": "要查詢的股票名稱或代碼，例如：台積電、Apple、2330、AAPL"
    }
  },
  "required": ["stock"]
}
```

---

## 2. 回應格式

### 2.1 成功回應

```json
{
  "success": true,
  "data": {
    "symbol": "2330.TW",
    "name": "台積電",
    "price": 1080.0,
    "currency": "TWD",
    "market": "TW",
    "queried_at": "2025-12-29T10:30:00+00:00"
  },
  "error": null
}
```

### 2.2 失敗回應

```json
{
  "success": false,
  "data": null,
  "error": "unsupported_stock: 抱歉，找不到這支股票，請確認名稱或代碼是否正確"
}
```

---

## 3. 錯誤代碼

| 錯誤前綴 | 說明 |
|----------|------|
| `unsupported_stock:` | 股票名稱/代碼不在支援列表中 |
| `api_error:` | yfinance API 回傳異常 |
| `no_data:` | API 回傳但無報價資料 |
| `network_error:` | 網路連線失敗 |
| `api_timeout:` | API 查詢逾時 |

---

## 4. 使用範例

### 4.1 台股查詢（中文名稱）

**輸入**:
```json
{"stock": "台積電"}
```

**輸出**:
```json
{
  "success": true,
  "data": {
    "symbol": "2330.TW",
    "name": "台積電",
    "price": 1080.0,
    "currency": "TWD",
    "market": "TW",
    "queried_at": "2025-12-29T10:30:00+00:00"
  },
  "error": null
}
```

### 4.2 台股查詢（代碼）

**輸入**:
```json
{"stock": "2330"}
```

**輸出**: 同上

### 4.3 美股查詢（英文名稱）

**輸入**:
```json
{"stock": "Apple"}
```

**輸出**:
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "name": "蘋果",
    "price": 254.50,
    "currency": "USD",
    "market": "US",
    "queried_at": "2025-12-29T10:30:00+00:00"
  },
  "error": null
}
```

### 4.4 美股查詢（中文名稱）

**輸入**:
```json
{"stock": "特斯拉"}
```

**輸出**:
```json
{
  "success": true,
  "data": {
    "symbol": "TSLA",
    "name": "特斯拉",
    "price": 430.20,
    "currency": "USD",
    "market": "US",
    "queried_at": "2025-12-29T10:30:00+00:00"
  },
  "error": null
}
```

### 4.5 無效股票

**輸入**:
```json
{"stock": "小明公司"}
```

**輸出**:
```json
{
  "success": false,
  "data": null,
  "error": "unsupported_stock: 抱歉，找不到這支股票，請確認名稱或代碼是否正確"
}
```

---

## 5. OpenAI Tool 格式

完整的 OpenAI Function Calling 工具定義：

```json
{
  "type": "function",
  "function": {
    "name": "get_stock_price",
    "description": "查詢股票即時報價。支援台股（台灣 50 成分股）與美股（S&P 500 前 30 大市值股票）。可使用中文名稱（如「台積電」、「蘋果」）、英文名稱（如「Apple」）或股票代碼（如「2330」、「AAPL」）查詢。",
    "parameters": {
      "type": "object",
      "properties": {
        "stock": {
          "type": "string",
          "description": "要查詢的股票名稱或代碼，例如：台積電、Apple、2330、AAPL"
        }
      },
      "required": ["stock"]
    }
  }
}
```

---

## 6. LLM 回應範例

根據工具回傳資料，LLM 應生成自然語言回應：

**台股回應**：
> 台積電目前的股價是 1,080 元。

**美股回應**：
> 蘋果目前的股價是 254.50 美元。

**錯誤回應**：
> 抱歉，找不到這支股票，請確認名稱或代碼是否正確。

**備註**（可選擇性加入）：
> 台積電目前的股價是 1,080 元。這是約 15 到 20 分鐘前的報價。
