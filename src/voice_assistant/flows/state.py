"""流程狀態與資料模型定義。

定義 LangGraph 流程所需的狀態類型與輔助函式。
"""

from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel

# 意圖類型
IntentType = Literal["weather", "exchange", "stock", "travel"]

# 建議類型
RecommendationType = Literal["outdoor", "indoor", "alternative_date"]


class WeatherInfo(BaseModel):
    """天氣資訊結構。"""

    city: str
    temperature: float
    weather: str
    weather_code: int
    humidity: float | None = None
    wind_speed: float | None = None


class TravelPlanState(TypedDict, total=False):
    """旅遊規劃子流程狀態。"""

    # 目的地解析
    destination: str | None
    destination_valid: bool

    # 天氣資訊
    weather_data: WeatherInfo | None
    weather_suitable: bool | None

    # 建議
    recommendation_type: RecommendationType | None
    recommendations: list[str]


class FlowState(TypedDict, total=False):
    """LangGraph 主流程狀態。"""

    # 輸入
    user_input: str

    # 意圖分類
    intent: IntentType

    # Tool 執行結果
    tool_name: str | None
    tool_args: dict | None
    tool_result: dict | None

    # 旅遊規劃（由子流程填充）
    travel_state: TravelPlanState | None

    # 輸出
    response: str
    error: str | None


def is_weather_suitable(weather_info: WeatherInfo) -> bool:
    """判斷天氣是否適合出遊。

    判斷條件：
    - 非雨天（天氣代碼不在下雨範圍內）
    - 氣溫介於 15-35°C

    Args:
        weather_info: 天氣資訊

    Returns:
        True 表示適合出遊，False 表示不適合
    """
    # 下雨天氣代碼：51-67, 80-82, 95-99
    rainy_codes = set(range(51, 68)) | set(range(80, 83)) | set(range(95, 100))

    is_not_rainy = weather_info.weather_code not in rainy_codes
    is_comfortable_temp = 15 <= weather_info.temperature <= 35

    return is_not_rainy and is_comfortable_temp


# 城市景點推薦清單
CITY_RECOMMENDATIONS: dict[str, dict[str, list[str]]] = {
    "台北": {
        "outdoor": ["象山步道", "陽明山國家公園", "淡水老街", "北投溫泉"],
        "indoor": ["台北101觀景台", "故宮博物院", "誠品書店", "西門町"],
    },
    "新北": {
        "outdoor": ["九份老街", "野柳地質公園", "平溪天燈", "烏來溫泉"],
        "indoor": ["林口三井Outlet", "板橋大遠百", "淡水漁人碼頭", "鶯歌陶瓷博物館"],
    },
    "桃園": {
        "outdoor": ["大溪老街", "石門水庫", "拉拉山", "小烏來天空步道"],
        "indoor": ["華泰名品城", "Xpark 水族館", "桃園機場觀景台", "中壢夜市"],
    },
    "台中": {
        "outdoor": ["高美濕地", "彩虹眷村", "東海大學", "台中公園"],
        "indoor": ["國立自然科學博物館", "逢甲夜市", "宮原眼科", "審計新村"],
    },
    "台南": {
        "outdoor": ["安平古堡", "四草綠色隧道", "漁光島", "井仔腳瓦盤鹽田"],
        "indoor": ["奇美博物館", "林百貨", "神農街", "國華街美食"],
    },
    "高雄": {
        "outdoor": ["西子灣", "旗津海岸", "蓮池潭", "駁二藝術特區"],
        "indoor": ["夢時代購物中心", "高雄市立美術館", "三多商圈", "瑞豐夜市"],
    },
    "基隆": {
        "outdoor": ["和平島公園", "正濱漁港彩色屋", "八斗子潮境公園", "基隆嶼"],
        "indoor": ["廟口夜市", "海洋科技博物館", "基隆文化中心", "仁愛市場"],
    },
    "新竹": {
        "outdoor": ["內灣老街", "青草湖", "十七公里海岸線", "新竹動物園"],
        "indoor": ["巨城購物中心", "城隍廟夜市", "玻璃工藝博物館", "新竹科學園區"],
    },
    "嘉義": {
        "outdoor": ["阿里山森林遊樂區", "檜意森活村", "蘭潭", "東石漁港"],
        "indoor": ["故宮南院", "嘉義文化路夜市", "森林之歌", "嘉義市立博物館"],
    },
    "屏東": {
        "outdoor": ["墾丁國家公園", "小琉球", "恆春古城", "龍磐公園"],
        "indoor": ["屏東菸葉廠", "屏東夜市", "海洋生物博物館", "恆春老街"],
    },
    "宜蘭": {
        "outdoor": ["太平山森林遊樂區", "外澳沙灘", "龜山島", "冬山河"],
        "indoor": ["羅東夜市", "宜蘭傳藝中心", "幾米廣場", "蘭陽博物館"],
    },
    "花蓮": {
        "outdoor": ["太魯閣國家公園", "七星潭", "清水斷崖", "瑞穗溫泉"],
        "indoor": ["東大門夜市", "花蓮文化創意園區", "松園別館", "慶修院"],
    },
    "台東": {
        "outdoor": ["三仙台", "伯朗大道", "鹿野高台", "綠島"],
        "indoor": ["台東鐵花村", "台東夜市", "國立臺灣史前文化博物館", "台東糖廠"],
    },
}
