"""Mock exchange rate API responses for testing."""

# T005: ExchangeRate-API mock 資料

# 成功回應 - USD 為基準
MOCK_EXCHANGE_RATE_USD = {
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
        "USD": 1,
        "TWD": 32.58,
        "JPY": 157.25,
        "EUR": 0.96,
        "CNY": 7.30,
        "KRW": 1450.0,
        "HKD": 7.78,
        "GBP": 0.79,
        "AUD": 1.61,
    },
}

# 成功回應 - TWD 為基準
MOCK_EXCHANGE_RATE_TWD = {
    "result": "success",
    "provider": "https://www.exchangerate-api.com",
    "documentation": "https://www.exchangerate-api.com/docs/free",
    "terms_of_use": "https://www.exchangerate-api.com/terms",
    "time_last_update_unix": 1735171351,
    "time_last_update_utc": "Thu, 26 Dec 2024 00:02:31 +0000",
    "time_next_update_unix": 1735259071,
    "time_next_update_utc": "Fri, 27 Dec 2024 00:24:31 +0000",
    "base_code": "TWD",
    "rates": {
        "TWD": 1,
        "USD": 0.0307,
        "JPY": 4.83,
        "EUR": 0.029,
        "CNY": 0.224,
        "KRW": 44.51,
        "HKD": 0.239,
        "GBP": 0.024,
        "AUD": 0.049,
    },
}

# 成功回應 - JPY 為基準
MOCK_EXCHANGE_RATE_JPY = {
    "result": "success",
    "provider": "https://www.exchangerate-api.com",
    "base_code": "JPY",
    "rates": {
        "JPY": 1,
        "TWD": 0.207,
        "USD": 0.00636,
        "EUR": 0.0061,
        "CNY": 0.0464,
        "KRW": 9.22,
        "HKD": 0.0495,
        "GBP": 0.00502,
        "AUD": 0.0102,
    },
}

# 錯誤回應 - API 錯誤
MOCK_EXCHANGE_RATE_ERROR = {
    "result": "error",
    "error-type": "unsupported-code",
}

# 不完整回應 - 缺少 rates
MOCK_EXCHANGE_RATE_MISSING_RATES = {
    "result": "success",
    "base_code": "USD",
}
