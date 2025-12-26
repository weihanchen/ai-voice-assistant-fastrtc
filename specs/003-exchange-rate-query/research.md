# Research: Exchange Rate Query Tool

## 1. Frankfurter API 研究

### Decision
使用 Frankfurter API 作為匯率資料來源。

### Rationale
- **Constitution 指定**：專案憲章明確規定匯率功能使用 Frankfurter API
- **免費且無需 API Key**：降低部署複雜度
- **支援 TWD**：支援新台幣作為基準貨幣
- **穩定可靠**：由歐洲中央銀行資料支援

### API Details

**Base URL**: `https://api.frankfurter.app`

**端點**:

| 端點 | 說明 | 範例 |
|------|------|------|
| `/latest` | 最新匯率 | `/latest?from=USD&to=TWD` |
| `/latest?amount=N` | 指定金額換算 | `/latest?amount=100&from=USD&to=TWD` |

**回應格式**:
```json
{
  "amount": 1,
  "base": "USD",
  "date": "2025-12-26",
  "rates": {
    "TWD": 32.5
  }
}
```

**支援貨幣**: USD, EUR, JPY, GBP, AUD, CNY, HKD, KRW 等主要貨幣（完整清單見 `/currencies`）

### Alternatives Considered

| API | 優點 | 缺點 | 結論 |
|-----|------|------|------|
| ExchangeRate-API | 更多貨幣 | 需要 API Key（免費版有限制） | ❌ 不採用 |
| Open Exchange Rates | 豐富功能 | 需要 API Key | ❌ 不採用 |
| Frankfurter | 免費、無需 Key、Constitution 指定 | 僅工作日更新 | ✅ 採用 |

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

### API Design

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
MOCK_EXCHANGE_RATE_USD_TWD = {
    "amount": 1,
    "base": "USD",
    "date": "2025-12-26",
    "rates": {"TWD": 32.5}
}

MOCK_EXCHANGE_RATE_JPY_TWD = {
    "amount": 1,
    "base": "JPY",
    "date": "2025-12-26",
    "rates": {"TWD": 0.22}
}
```
