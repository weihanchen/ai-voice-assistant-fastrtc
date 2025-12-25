"""Mock weather API responses for testing."""

# T007: Open-Meteo API mock 資料

# 成功回應 - 基本資訊
MOCK_WEATHER_BASIC = {
    "latitude": 25.03,
    "longitude": 121.5625,
    "current_units": {
        "temperature_2m": "°C",
        "weather_code": "wmo code",
    },
    "current": {
        "temperature_2m": 22.5,
        "weather_code": 3,  # 陰天
    },
}

# 成功回應 - 詳細資訊
MOCK_WEATHER_DETAILED = {
    "latitude": 25.03,
    "longitude": 121.5625,
    "current_units": {
        "temperature_2m": "°C",
        "weather_code": "wmo code",
        "relative_humidity_2m": "%",
        "apparent_temperature": "°C",
        "wind_speed_10m": "km/h",
    },
    "current": {
        "temperature_2m": 22.5,
        "weather_code": 3,  # 陰天
        "relative_humidity_2m": 75,
        "apparent_temperature": 24.1,
        "wind_speed_10m": 12.3,
    },
}

# 晴天回應
MOCK_WEATHER_SUNNY = {
    "latitude": 22.63,
    "longitude": 120.30,
    "current_units": {
        "temperature_2m": "°C",
        "weather_code": "wmo code",
    },
    "current": {
        "temperature_2m": 28.0,
        "weather_code": 0,  # 晴朗
    },
}

# 雨天回應
MOCK_WEATHER_RAINY = {
    "latitude": 24.15,
    "longitude": 120.67,
    "current_units": {
        "temperature_2m": "°C",
        "weather_code": "wmo code",
    },
    "current": {
        "temperature_2m": 18.5,
        "weather_code": 61,  # 小雨
    },
}
