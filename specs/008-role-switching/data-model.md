# Data Model: 角色切換系統

**Date**: 2025-01-25  
**Feature**: 008-role-switching  
**Phase**: 1 - Data Model Design

## Entity Overview

本系統定義了角色切換功能的核心資料模型，遵循 Pydantic 資料驗證和型別安全原則。

## Core Entities

### 1. Role (角色)

角色是 AI 對話行為的抽象定義，包含語氣風格、系統提示詞等屬性。

```python
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator
from datetime import datetime

class RoleType(str, Enum):
    INTERVIEWER = "interviewer"    # 面試官
    ASSISTANT = "assistant"        # 助理
    COACH = "coach"               # 教練
    CUSTOM = "custom"             # 自定義

class Role(BaseModel):
    """AI 角色定義"""
    
    # 基本屬性
    id: str = Field(..., description="角色唯一識別碼")
    name: str = Field(..., description="角色顯示名稱")
    role_type: RoleType = Field(..., description="角色類型")
    
    # 行為定義
    system_prompt: str = Field(..., description="LLM 系統提示詞")
    tone_style: str = Field(..., description="語氣風格描述")
    
    # 流程模式配置 (新增於 2025-01-26)
    preferred_flow_mode: Optional[str] = Field(
        None, 
        description="角色專屬流程模式 (multi_agent/langgraph/tools)，若設定則覆蓋全域 FLOW_MODE"
    )
    
    # 元資料
    description: Optional[str] = Field(None, description="角色描述")
    example_responses: List[str] = Field(default_factory=list, description="範例回應")
    welcome_message: Optional[str] = Field(None, description="角色切換時的歡迎訊息")
    
    # 配置
    is_active: bool = Field(True, description="是否啟用")
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    updated_at: Optional[datetime] = Field(None, description="更新時間")
    
    class Config:
        use_enum_values = True
    
    @validator('system_prompt')
    def validate_system_prompt(cls, v):
        if not v.strip():
            raise ValueError('系統提示詞不能為空')
        return v.strip()
    
    @validator('id')
    def validate_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('角色 ID 不能為空')
        return v.strip().lower()
```

### 2. RoleState (角色狀態)

維護當前活躍角色和切換歷史記錄。

```python
from typing import Optional, List
from pydantic import BaseModel, Field

class RoleTransition(BaseModel):
    """角色切換記錄"""
    from_role: Optional[str] = Field(None, description="來源角色 ID")
    to_role: str = Field(..., description="目標角色 ID")
    reason: str = Field(..., description="切換原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="切換時間")

class RoleState(BaseModel):
    """角色狀態管理器"""
    
    # 當前狀態
    current_role_id: Optional[str] = Field(None, description="當前角色 ID")
    
    # 歷史記錄
    transition_history: List[RoleTransition] = Field(
        default_factory=list, 
        description="角色切換歷史",
        max_items=50  # 限制歷史記錄數量
    )
    
    # 狀態元資料
    session_id: str = Field(..., description="對話會話 ID")
    created_at: datetime = Field(default_factory=datetime.now, description="會話開始時間")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
    
    def add_transition(self, from_role: str, to_role: str, reason: str):
        """新增角色切換記錄"""
        transition = RoleTransition(
            from_role=from_role,
            to_role=to_role,
            reason=reason
        )
        self.transition_history.append(transition)
        self.last_updated = datetime.now()
```

### 3. Intent (意圖)

定義角色切換的意圖識別模型。

```python
class IntentType(str, Enum):
    ROLE_SWITCH = "role_switch"      # 角色切換
    ROLE_QUERY = "role_query"         # 角色查詢
    ROLE_LIST = "role_list"           # 角色列表
    UNKNOWN = "unknown"               # 未知意圖

class Intent(BaseModel):
    """意圖識別結果"""
    
    # 基本屬性
    intent_type: IntentType = Field(..., description="意圖類型")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心分數")
    
    # 角色切換專用
    target_role: Optional[str] = Field(None, description="目標角色")
    
    # 元資料
    original_text: str = Field(..., description="原始輸入文字")
    processing_time_ms: int = Field(..., description="處理時間（毫秒）")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if v < 0.5:
            raise ValueError('信心分數必須大於等於 0.5')
        return v
    
    @validator('target_role')
    def validate_target_role(cls, v, values):
        if values.get('intent_type') == IntentType.ROLE_SWITCH and not v:
            raise ValueError('角色切換意圖必須指定目標角色')
        return v
```

### 4. RoleRegistryConfig (角色註冊配置)

角色註冊表的配置和管理。

```python
class RoleRegistryConfig(BaseModel):
    """角色註冊表配置"""
    
    # 註冊的角色
    roles: Dict[str, Role] = Field(default_factory=dict, description="已註冊的角色")
    
    # 配置
    default_role_id: Optional[str] = Field(None, description="預設角色 ID")
    max_roles: int = Field(50, description="最大角色數量")
    
    # 統計
    total_registrations: int = Field(default=0, description="總註冊次數")
    
    def register_role(self, role: Role) -> bool:
        """註冊新角色"""
        if len(self.roles) >= self.max_roles:
            return False
        
        self.roles[role.id] = role
        self.total_registrations += 1
        return True
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """獲取角色"""
        return self.roles.get(role_id)
    
    def list_roles(self) -> List[Role]:
        """列出所有角色"""
        return list(self.roles.values())
```

## Data Relationships

```mermaid
erDiagram
    Role ||--o{ RoleTransition : creates
    RoleState ||--o{ RoleTransition : contains
    Role ||--|| IntentType : defines
    
    Role {
        string id PK
        string name
        RoleType role_type
        string system_prompt
        string tone_style
        string preferred_flow_mode
        string welcome_message
        datetime created_at
    }
    
    RoleState {
        string session_id PK
        string current_role_id FK
        datetime created_at
        datetime last_updated
    }
    
    RoleTransition {
        datetime timestamp
        string from_role_id FK
        string to_role_id FK
        string reason
    }
    
    Intent {
        IntentType intent_type
        float confidence
        string target_role
        string original_text
        int processing_time_ms
    }
```

## Validation Rules

### 角色驗證

1. **ID 唯一性**: 角色 ID 必須唯一
2. **提示詞完整性**: 系統提示詞不能為空
3. **枚舉有效性**: 角色類型必須為有效枚舉值
4. **長度限制**: 角色名稱 <= 50 字符

### 狀態驗證

1. **會話唯一性**: 會話 ID 必須唯一
2. **歷史限制**: 切換歷史最多保留 50 條記錄
3. **時間一致性**: 更新時間不能早於建立時間

### 意圖驗證

1. **信心分數**: 必須 >= 0.5
2. **一致性**: 角色切換意圖必須指定目標角色
3. **處理時間**: 必須為正整數

## State Transitions

### 角色切換狀態轉換

```mermaid
stateDiagram-v2
    [*] --> NoRole
    NoRole --> Interviewer: switch to interviewer
    NoRole --> Assistant: switch to assistant
    NoRole --> Coach: switch to coach
    
    Interviewer --> Assistant: switch to assistant
    Interviewer --> Coach: switch to coach
    Interviewer --> Interviewer: switch to interviewer (no-op)
    
    Assistant --> Interviewer: switch to interviewer
    Assistant --> Coach: switch to coach
    Assistant --> Assistant: switch to assistant (no-op)
    
    Coach --> Interviewer: switch to interviewer
    Coach --> Assistant: switch to assistant
    Coach --> Coach: switch to coach (no-op)
```

### 流程模式選擇邏輯 (新增於 2025-01-26)

此流程圖說明當使用者輸入訊息時，系統如何根據角色的 `preferred_flow_mode` 決定使用哪種處理流程。

```mermaid
flowchart TD
    Start([收到使用者輸入]) --> CheckIntent{是否為<br/>角色切換指令?}
    
    CheckIntent -->|是| SwitchRole[執行角色切換]
    SwitchRole --> PlayWelcome[播放歡迎訊息]
    PlayWelcome --> End([結束])
    
    CheckIntent -->|否| GetRole[取得當前角色]
    GetRole --> HasRole{角色是否存在?}
    
    HasRole -->|否| UseGlobal[使用全域 FLOW_MODE]
    HasRole -->|是| CheckPreferred{角色有<br/>preferred_flow_mode?}
    
    CheckPreferred -->|否| UseGlobal
    CheckPreferred -->|是| UsePreferred[使用角色專屬<br/>flow_mode]
    
    UseGlobal --> LogGlobal[LOG: 使用全域流程模式]
    UsePreferred --> LogPreferred[LOG: 使用角色專屬流程模式]
    
    LogGlobal --> DetermineMode{判斷流程模式}
    LogPreferred --> DetermineMode
    
    DetermineMode -->|multi_agent| MultiAgent[Multi-Agent 流程<br/>Supervisor 分派任務]
    DetermineMode -->|langgraph| LangGraph[LangGraph 流程<br/>狀態機處理]
    DetermineMode -->|tools| Tools[Tool Calling 流程<br/>純 LLM + 工具]
    
    MultiAgent --> ProcessMsg[處理訊息]
    LangGraph --> ProcessMsg
    Tools --> ProcessMsg
    
    ProcessMsg --> GenResponse[生成回應]
    GenResponse --> PlayTTS[播放 TTS]
    PlayTTS --> End
    
    style UsePreferred fill:#90EE90
    style MultiAgent fill:#FFE4B5
    style LangGraph fill:#FFE4B5
    style Tools fill:#FFE4B5
    style LogPreferred fill:#87CEEB
```

### 角色與流程模式對應表

| 角色 ID | 角色名稱 | preferred_flow_mode | 說明 |
|---------|----------|---------------------|------|
| `assistant` | 助理 | `multi_agent` | 任務導向，使用 Supervisor 智能分派 |
| `interviewer` | 面試官 | `tools` | 對話導向，使用純 LLM + Tool Calling |
| `coach` | 教練 | `tools` | 對話導向，使用純 LLM + Tool Calling |

### 流程模式說明

1. **multi_agent 模式**
   - 適用於：任務導向的查詢（天氣、匯率、股價等）
   - 特點：Supervisor 代理分析使用者需求，分派給專業代理（WeatherAgent、FinanceAgent 等）
   - 優點：智能路由、專業分工、複雜任務處理能力強
   - 缺點：對話互動較生硬，不適合面試或教練場景

2. **langgraph 模式**
   - 適用於：需要多步驟推理的複雜流程
   - 特點：使用狀態機管理對話流程，支援條件分支和循環
   - 優點：流程可視化、狀態管理清晰
   - 缺點：配置複雜，目前未大量使用

3. **tools 模式**
   - 適用於：對話導向的場景（面試、教練、一般聊天）
   - 特點：純 LLM 處理，根據需要調用工具
   - 優點：對話自然、回應連貫、適合人際互動
   - 缺點：複雜任務處理能力較弱

## Error Handling

### 常見錯誤

1. **角色不存在**: `RoleNotFoundError`
2. **無效切換**: `InvalidRoleSwitchError`
3. **註冊限制**: `RoleRegistrationLimitError`
4. **意圖識別失敗**: `IntentRecognitionError`

### 錯誤回應格式

```python
class RoleError(BaseModel):
    """角色相關錯誤"""
    error_type: str = Field(..., description="錯誤類型")
    error_message: str = Field(..., description="錯誤訊息")
    context: Dict[str, Any] = Field(default_factory=dict, description="錯誤上下文")
    timestamp: datetime = Field(default_factory=datetime.now)
```

## Performance Considerations

### 記憶體使用

- **角色定義**: 每個角色約 1-2KB
- **狀態管理**: 每個會話約 1KB
- **總計**: 10 個角色 + 1 個會話 < 25KB

### 查詢效能

- **角色查找**: O(1) 哈希表查找
- **切換操作**: O(1) 狀態更新
- **歷史查詢**: O(n) 線性搜尋（限制 n <= 50）

## Future Extensions

### 支援的功能

1. **角色繼承**: 允許角色繼承其他角色的屬性
2. **角色版本**: 支援角色定義的版本控制
3. **角色組合**: 支援多個角色的組合使用
4. **持久化**: 可選的資料庫持久化支援

### 向後兼容性

- 所有現有欄位保持不變
- 新增欄位使用 Optional 類型
- 保持 API 介面穩定性