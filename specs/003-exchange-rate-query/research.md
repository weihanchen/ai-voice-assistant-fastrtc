# Research: Exchange Rate Query Tool

## 1. ExchangeRate-API 研究

### Decision
使用 ExchangeRate-API (Open Access) 作為匯率資料來源。

### Rationale
- **支援 TWD**：確認支援新台幣（已實測驗證）
- **免費且無需 API Key**：Open Access 端點無需註冊
- **穩定可靠**：提供 150+ 種貨幣的即時匯率

### API Details

**Base URL**: `https://open.er-api.com/v6/latest`

**端點**:

| 端點 | 說明 | 範例 |
|------|------|------|
| `/latest/{base}` | 取得指定貨幣對所有貨幣的匯率 | `/latest/USD` |

**回應格式**:
```json
{
  "result": "success",
  "provider": "https://www.exchangerate-api.com",
  "documentation": "https://www.exchangerate-api.com/docs/free",
  "terms_of_use": "https://www.exchangerate-api.com/terms",
  "time_last_update_unix": 1735171351,
  "time_last_update_utc": "Thu, 26 Dec 2024 00:02:31 +0000",
  "time_next_update_unix": 1735259071,
  "time_next_update_utc": "Fri, 27 Dec 2024 00:24:31 +0000",
  "base_code": "USD",
  "rates": {
    "TWD": 32.58,
    "JPY": 157.25,
    "EUR": 0.96,
    ...
  }
}
```

**支援貨幣**: USD, EUR, JPY, GBP, AUD, CNY, HKD, KRW, TWD 等 150+ 種貨幣

**實測驗證**:
```bash
curl "https://open.er-api.com/v6/latest/USD"
# 回應包含 "TWD": 32.58（實際值）
```

### Alternatives Considered

| API | 優點 | 缺點 | 結論 |
|-----|------|------|------|
| Frankfurter | 免費、無需 Key | **不支援 TWD** | ❌ 不採用 |
| Open Exchange Rates | 豐富功能 | 需要 API Key | ❌ 不採用 |
| ExchangeRate-API | 免費、無需 Key、**支援 TWD** | 每日更新 | ✅ 採用 |

### 注意事項

- Open Access 版本有速率限制，建議每 24 小時查詢一次以避免限制
- 可快取匯率資料 5-10 分鐘以減少 API 呼叫

---

## 2. 貨幣代碼標準化

### Decision
建立貨幣別名對照表，將中文貨幣名稱映射到 ISO 4217 代碼。

### Rationale
- 使用者會用中文詢問（如「美金」、「日幣」）
- STT 輸出可能有變體（「美元」vs「美金」）
- 需要統一轉換為 API 接受的 ISO 代碼

### Currency Mapping

```python
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
```

### Currency Display Names

```python
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
```

---

## 3. 換算邏輯設計

### Decision
支援三種換算模式：

1. **查詢匯率**：`get_exchange_rate(from_currency, to_currency)` → 回傳 1 單位匯率
2. **金額換算**：`convert_currency(amount, from_currency, to_currency)` → 回傳換算結果
3. **預設 TWD**：當只指定一種貨幣時，自動以 TWD 為對應貨幣

### Rationale
- 符合使用者自然語言習慣（「美金匯率」= USD→TWD）
- 支援雙向換算（USD→TWD 和 TWD→USD）
- 簡化 LLM 的 Function Calling 參數

### API 呼叫策略

由於 ExchangeRate-API 只提供 `/latest/{base}` 端點，換算邏輯如下：

```python
# 查詢 USD → TWD
response = await client.get(f"{BASE_URL}/latest/USD")
rate = response["rates"]["TWD"]  # 例如 32.58

# 查詢 TWD → USD（需要反向計算）
response = await client.get(f"{BASE_URL}/latest/TWD")
rate = response["rates"]["USD"]  # 例如 0.0307
```

### Tool Execute Signature

```python
async def execute(
    self,
    from_currency: str,
    to_currency: str = "TWD",
    amount: float = 1.0
) -> ToolResult:
    """
    執行匯率查詢或換算。

    Args:
        from_currency: 來源貨幣（中文或 ISO 代碼）
        to_currency: 目標貨幣（預設 TWD）
        amount: 換算金額（預設 1.0）

    Returns:
        ToolResult: 包含匯率和換算結果
    """
```

---

## 4. 錯誤處理策略

### Decision
定義明確的錯誤類型與友善訊息。

### Error Types

| 錯誤類型 | 觸發條件 | 回應訊息 |
|----------|----------|----------|
| `unsupported_currency` | 貨幣不在支援清單 | 「抱歉，目前僅支援主要國際貨幣，例如美金、日幣、歐元、人民幣等」 |
| `same_currency` | 來源與目標相同 | 「您查詢的是相同貨幣，無需換算」 |
| `invalid_amount` | 金額 ≤ 0 | 「請提供有效的金額」 |
| `api_timeout` | API 逾時 | 「抱歉，目前無法取得匯率資訊，請稍後再試」 |
| `network_error` | 網路錯誤 | 「網路連線異常，請檢查網路狀態」 |
| `api_error` | API 回傳錯誤 | 「無法取得匯率資訊，請稍後再試」 |

---

## 5. 與 WeatherTool 的一致性

### Decision
遵循 WeatherTool 的實作模式，確保程式碼風格一致。

### Patterns to Follow

| 模式 | WeatherTool 範例 | ExchangeRateTool 應用 |
|------|------------------|----------------------|
| 常數定義 | `TAIWAN_CITIES`, `WEATHER_CODES` | `CURRENCY_ALIASES`, `CURRENCY_NAMES` |
| 別名解析 | `_resolve_city()` | `_resolve_currency()` |
| API 呼叫 | `_fetch_weather()` | `_fetch_exchange_rate()` |
| 錯誤處理 | `ToolResult.fail()` | 相同模式 |
| 輸入正規化 | `city.strip().replace("\u3000", "")` | 相同模式 |

---

## 6. 測試策略

### Unit Tests

| 測試類別 | 測試項目 |
|----------|----------|
| 屬性測試 | `name`, `description`, `parameters` |
| 貨幣解析 | 標準名稱、別名、不支援貨幣 |
| 匯率查詢 | 成功查詢、API 錯誤、網路錯誤 |
| 金額換算 | 正常金額、無效金額、相同貨幣 |
| 邊界案例 | 空白輸入、全形空白、大小寫 |

### Mock Data

```python
MOCK_EXCHANGE_RATE_USD = {
    "result": "success",
    "base_code": "USD",
    "rates": {
        "TWD": 32.58,
        "JPY": 157.25,
        "EUR": 0.96,
    }
}

MOCK_EXCHANGE_RATE_TWD = {
    "result": "success",
    "base_code": "TWD",
    "rates": {
        "USD": 0.0307,
        "JPY": 4.83,
        "EUR": 0.029,
    }
}
```
