# Data Model: Exchange Rate Query Tool

## Entities

### Currency

貨幣資訊，用於解析使用者輸入並標準化為 ISO 4217 代碼。

| 屬性 | 型別 | 說明 | 範例 |
|------|------|------|------|
| `code` | str | ISO 4217 貨幣代碼 | `"USD"`, `"JPY"` |
| `name` | str | 中文顯示名稱 | `"美元"`, `"日圓"` |
| `aliases` | list[str] | 別名清單 | `["美金", "美元", "美刀"]` |

**Validation Rules**:
- `code` 必須為 3 個大寫英文字母
- `name` 必須為非空字串
- `aliases` 可為空清單

**Supported Currencies**:

| Code | Name | Aliases |
|------|------|---------|
| USD | 美元 | 美金, 美元, 美刀 |
| JPY | 日圓 | 日幣, 日圓, 日元 |
| EUR | 歐元 | 歐元 |
| CNY | 人民幣 | 人民幣, 人民币 |
| KRW | 韓元 | 韓元, 韓幣 |
| HKD | 港幣 | 港幣, 港元 |
| GBP | 英鎊 | 英鎊 |
| AUD | 澳幣 | 澳幣, 澳元 |
| TWD | 新台幣 | 台幣, 新台幣 |

---

### ExchangeRateData

匯率資料，對應 Frankfurter API 回應。

| 屬性 | 型別 | 說明 | 範例 |
|------|------|------|------|
| `base` | str | 基準貨幣 | `"USD"` |
| `target` | str | 目標貨幣 | `"TWD"` |
| `rate` | float | 匯率值 | `32.5` |
| `date` | str | 資料日期 | `"2025-12-26"` |

**Validation Rules**:
- `base` 和 `target` 必須為有效貨幣代碼
- `rate` 必須 > 0
- `date` 必須為有效日期格式 (YYYY-MM-DD)

**API Response Mapping**:

```json
// ExchangeRate-API Response
{
  "result": "success",
  "base_code": "USD",
  "time_last_update_utc": "Thu, 26 Dec 2024 00:02:31 +0000",
  "rates": {
    "TWD": 32.58,
    "JPY": 157.25
  }
}
```

映射為:
```python
ExchangeRateData(
    base="USD",
    target="TWD",
    rate=32.58,
    date="2024-12-26"
)
```

---

### ConversionResult

換算結果，用於 Tool 回應。

| 屬性 | 型別 | 說明 | 範例 |
|------|------|------|------|
| `from_currency` | str | 來源貨幣代碼 | `"USD"` |
| `from_amount` | float | 來源金額 | `100.0` |
| `to_currency` | str | 目標貨幣代碼 | `"TWD"` |
| `to_amount` | float | 換算後金額 | `3250.0` |
| `rate` | float | 使用的匯率 | `32.5` |
| `queried_at` | str | 查詢時間 (ISO 8601) | `"2025-12-26T12:00:00+00:00"` |

**Validation Rules**:
- `from_amount` 必須 > 0
- `to_amount` = `from_amount` × `rate`
- `queried_at` 必須為 ISO 8601 格式

---

## State Diagram

```
┌─────────────┐
│   使用者    │
│   語音輸入  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  解析貨幣   │──────────┐
│  名稱/別名  │          │ 無法識別
└──────┬──────┘          ▼
       │           ┌─────────────┐
       │           │ 回傳錯誤    │
       │           │ unsupported │
       │           └─────────────┘
       ▼
┌─────────────┐
│  檢查貨幣   │──────────┐
│  是否相同   │          │ 相同
└──────┬──────┘          ▼
       │           ┌─────────────┐
       │ 不同      │ 回傳錯誤    │
       │           │ same_currency│
       │           └─────────────┘
       ▼
┌─────────────┐
│  呼叫 API   │──────────┐
│  查詢匯率   │          │ 失敗
└──────┬──────┘          ▼
       │           ┌─────────────┐
       │ 成功      │ 回傳錯誤    │
       │           │ api_error   │
       │           └─────────────┘
       ▼
┌─────────────┐
│  計算換算   │
│  結果      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  回傳結果   │
│  ToolResult │
└─────────────┘
```

---

## Relationships

```
Currency (1) ──────< (N) CURRENCY_ALIASES
    │
    │ resolved to
    ▼
ExchangeRateData ──────> ConversionResult
    │                         │
    │ from API               │ calculated
    ▼                         ▼
Frankfurter API         ToolResult.ok(data)
```
