# Research: Stock Price Query

**Feature**: 004-stock-price-query
**Date**: 2025-12-29

## 研究主題

1. yfinance 套件用法與台股支援
2. 股票代碼對照表設計
3. 錯誤處理策略

---

## 1. yfinance 套件用法

### Decision: 使用 `fast_info.last_price` 取得即時報價

### Rationale

- `fast_info` 是 yfinance v0.2.14+ 引入的輕量級 API，專為速度優化
- 比 `stock.info['regularMarketPrice']` 更快（不載入完整公司資訊）
- 適合語音助理的低延遲需求

### 程式碼範例

```python
import yfinance as yf

# 台股（需加 .TW 後綴）
tsmc = yf.Ticker("2330.TW")
price = tsmc.fast_info.last_price
currency = tsmc.fast_info.currency  # 'TWD'

# 美股（直接使用代碼）
apple = yf.Ticker("AAPL")
price = apple.fast_info.last_price
currency = apple.fast_info.currency  # 'USD'
```

### 台股代碼格式

| 格式 | 說明 | 範例 |
|------|------|------|
| `{代碼}.TW` | 台灣上市股票 | 2330.TW |
| `{代碼}.TWO` | 台灣上櫃股票 | 6488.TWO |
| `^TWII` | 台灣加權指數 | - |

### 注意事項

- yfinance 報價有 15-20 分鐘延遲（免費版限制）
- 每 IP 每小時限制 2,000 請求
- API 可能因 Yahoo 網站變更而失效，需保持更新

### Alternatives Considered

| 方案 | 優點 | 缺點 | 結論 |
|------|------|------|------|
| `stock.info['regularMarketPrice']` | 資料完整 | 較慢，載入多餘資訊 | 不採用 |
| `stock.history(period="1d")` | 取得歷史資料 | 需額外處理取最新價 | 不採用 |
| twstock 套件 | 台股專用，即時資料 | 僅支援台股，無美股 | 不採用 |

---

## 2. 股票代碼對照表設計

### Decision: 硬編碼對照表，分為台股與美股兩個字典

### Rationale

- 規格要求：台灣 50 成分股 + 美股前 30 大
- 約 80 支股票，硬編碼維護成本低
- 支援中文別名、英文名稱、股票代碼三種查詢方式

### 對照表結構

```python
# 台股對照表
TW_STOCK_ALIASES: dict[str, str] = {
    # 中文名稱 → 股票代碼（含 .TW 後綴）
    "台積電": "2330.TW",
    "鴻海": "2317.TW",
    "聯發科": "2454.TW",
    # 股票代碼（不含後綴）→ 完整代碼
    "2330": "2330.TW",
    "2317": "2317.TW",
    # ...
}

# 美股對照表
US_STOCK_ALIASES: dict[str, str] = {
    # 中文名稱 → 股票代碼
    "蘋果": "AAPL",
    "微軟": "MSFT",
    "特斯拉": "TSLA",
    # 英文名稱 → 股票代碼
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    # 代碼本身（大寫）
    "AAPL": "AAPL",
    # ...
}
```

### 查詢邏輯

1. 正規化輸入（去空白、處理全形字元）
2. 先查台股對照表
3. 再查美股對照表（大小寫不敏感）
4. 若都找不到，回傳錯誤

### Alternatives Considered

| 方案 | 優點 | 缺點 | 結論 |
|------|------|------|------|
| 硬編碼字典 | 簡單、可控、效能好 | 需手動維護 | ✅ 採用 |
| 外部 JSON 檔 | 易於更新 | 增加檔案 I/O | 不採用 |
| 動態 API 查詢 | 資料最新 | 延遲高、複雜度高 | 不採用 |

---

## 3. 錯誤處理策略

### Decision: 分層錯誤處理，提供友善中文錯誤訊息

### 錯誤類型與處理

| 錯誤類型 | 原因 | 回應 |
|----------|------|------|
| `unsupported_stock` | 股票名稱/代碼不在對照表 | 「抱歉，找不到這支股票，請確認名稱或代碼是否正確」 |
| `api_error` | yfinance API 回傳異常 | 「股票服務暫時無法使用，請稍後再試」 |
| `no_data` | API 回傳但無報價資料 | 「無法取得報價資訊，該股票可能已下市或暫停交易」 |
| `network_error` | 網路連線失敗 | 「網路連線異常，請檢查網路狀態」 |
| `timeout` | API 逾時 | 「股票查詢逾時，請稍後再試」 |

### 實作考量

- yfinance 是同步套件，需用 `asyncio.to_thread()` 包裝為非同步
- 設定合理逾時時間（建議 8 秒）
- 驗證 `fast_info.last_price` 是否為有效數值

---

## 4. 股票名稱顯示

### Decision: 建立反向對照表供回應使用

### Rationale

回應時需要顯示股票的中文名稱，而非只有代碼：
「台積電目前股價是 1,080 元」而非「2330.TW 目前股價是 1,080 元」

### 結構

```python
# 股票代碼 → 中文顯示名稱
STOCK_DISPLAY_NAMES: dict[str, str] = {
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "AAPL": "蘋果",
    "TSLA": "特斯拉",
    # ...
}
```

---

## 參考資料

- [yfinance PyPI](https://pypi.org/project/yfinance/)
- [yfinance fast_info 說明](https://www.pythontutorials.net/blog/how-to-get-actual-stock-prices-with-yfinance/)
- [台股代碼格式說明](https://www.pj-worklife.com.tw/yfinance-api/)
- [Quote and Fast Info System](https://deepwiki.com/ranaroussi/yfinance/5.2-quote-and-fast-info-system)
