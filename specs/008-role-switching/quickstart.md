# 角色切換功能快速開始指南

**版本**: 1.0.0  
**更新**: 2025-01-25  
**適用**: 開發者、系統整合者

## 概述

角色切換功能為 AI 語音助理提供動態角色切換能力，支援面試官、助理、教練等預設角色，並可通過語音指令或 UI 介面進行切換。

## 快速體驗

### 1. 啟動系統

```bash
# 啟動開發環境
uv run python -m voice_assistant.main

# 系統將自動啟動 FastRTC 服務和 Gradio UI
# 預設地址: http://localhost:7860
```

### 2. 基礎角色切換

#### 語音指令切換

對著麥克風說：
- "請切換到面試官"
- "切換到助理"
- "變成教練"

#### UI 介面切換

1. 打開 Gradio 介面
2. 在角色選擇器中選擇目標角色
3. 系統會立即切換並確認

### 3. 體驗不同角色

#### 面試官角色
```
你: 我是軟體工程師，有3年經驗
AI: 可以請您詳細說明一下您主要負責的專案類型嗎？
```

#### 助理角色  
```
你: 幫我安排會議
AI: 好的，請告訴我會議的主題、時間和參與者。
```

#### 教練角色
```
你: 我想要學習新技能
AI: 很好的想法！你對學習什麼樣的技能感興趣呢？
```

## 開發者整合

### 1. 基礎角色定義

```python
from voice_assistant.roles.base import BaseRole
from voice_assistant.roles.schemas import RoleType

class CustomRole(BaseRole):
    @property
    def id(self) -> str:
        return "custom-role"
    
    @property
    def name(self) -> str:
        return "自定義角色"
    
    @property
    def role_type(self) -> RoleType:
        return RoleType.CUSTOM
    
    @property
    def system_prompt(self) -> str:
        return """你是一個自定義角色，專門協助使用者解決特定問題。
請保持友善、專業的語氣，並提供具體可行的建議。"""
    
    @property
    def tone_style(self) -> str:
        return "友善、專業、鼓勵性"
```

### 2. 角色註冊

```python
from voice_assistant.roles.registry import RoleRegistry

# 註冊新角色
registry = RoleRegistry()
registry.register_role(CustomRole())

# 獲取角色
role = registry.get_role("custom-role")
```

### 3. 角色切換

```python
from voice_assistant.roles.state import RoleState

# 初始化狀態管理器
role_state = RoleState(session_id="user-session-123")

# 切換角色
success = role_state.switch_to("interviewer", reason="user_voice_command")
if success:
    print("角色切換成功")
    
# 獲取當前角色
current_role = role_state.get_current()
```

### 4. LLM 整合

```python
from voice_assistant.llm.client import LLMClient

# 初始化 LLM 客戶端
llm_client = LLMClient()

# 根據當前角色更新系統提示詞
current_role = role_state.get_current()
llm_client.update_system_prompt(current_role.system_prompt)

# 進行對話
response = await llm_client.chat(messages)
```

### 5. 意圖識別整合

```python
from voice_assistant.intent.recognizer import IntentRecognizer

# 初始化意圖識別器
recognizer = IntentRecognizer()

# 識別用戶意圖
intent = await recognizer.recognize("請切換到面試官", session_id="session-123")

if intent.intent_type == IntentType.ROLE_SWITCH:
    # 執行角色切換
    role_state.switch_to(intent.target_role, reason="user_voice_command")
```

## API 使用範例

### 1. 角色管理

```bash
# 獲取角色列表
curl -H "Authorization: Bearer {token}" \
     http://localhost:8000/internal/api/roles

# 獲取特定角色
curl -H "Authorization: Bearer {token}" \
     http://localhost:8000/internal/api/roles/interviewer
```

### 2. 角色狀態操作

```bash
# 切換角色
curl -X POST \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "session-123", "target_role_id": "interviewer", "reason": "user_voice_command"}' \
     http://localhost:8000/internal/api/role-state/switch

# 獲取當前狀態
curl -H "Authorization: Bearer {token}" \
     http://localhost:8000/internal/api/role-state/session-123
```

### 3. 意圖識別

```bash
# 識別意圖
curl -X POST \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{"text": "請切換到面試官", "session_id": "session-123"}' \
     http://localhost:8000/internal/api/intent/recognize
```

## 測試指南

### 1. 單元測試

```bash
# 執行角色系統測試
uv run pytest tests/unit/roles/ -v

# 執行意圖識別測試
uv run pytest tests/unit/intent/ -v

# 執行 UI 組件測試
uv run pytest tests/unit/ui/ -v
```

### 2. 整合測試

```bash
# 執行角色切換整合測試
uv run pytest tests/integration/test_role_switching.py -v

# 執行端對端測試
uv run pytest tests/integration/test_e2e_voice_interaction.py -v
```

### 3. 手動測試

使用 Gradio 介面進行手動測試：

1. **角色切換測試**
   - 測試所有預設角色的切換
   - 驗證切換後的對話風格變化
   - 測試重複切換同一角色

2. **語音指令測試**
   - 測試各種表達方式的切換指令
   - 驗證識別準確性
   - 測試噪音環境下的表現

3. **錯誤處理測試**
   - 測試切換到不存在角色
   - 測試無效輸入處理
   - 驗證錯誤訊息的友善性

## 常見問題

### Q1: 如何添加新的預設角色？

在 `src/voice_assistant/roles/predefined/` 目錄下建立新角色檔案：

```python
# src/voice_assistant/roles/predefined/mentor.py
class MentorRole(BaseRole):
    @property
    def id(self) -> str:
        return "mentor"
    
    @property
    def name(self) -> str:
        return "導師"
    
    # ... 其他屬性定義
```

然後在 `src/voice_assistant/roles/registry.py` 中註冊。

### Q2: 角色切換是否會影響對話歷史？

角色切換只會影響後續的對話風格，不會清除對話歷史。系統會記錄切換時間點，但保持上下文連續性。

### Q3: 如何自訂角色的回應風格？

通過修改角色的 `system_prompt` 和 `tone_style` 屬性：

```python
@property
def system_prompt(self) -> str:
    return """你是一位幽默的程式設計師，喜歡用程式梗來解釋複雜概念。
請保持輕鬆有趣的語氣，但確保內容的準確性。"""
```

### Q4: 如何監控角色切換的效能？

系統提供內建的監控指標：

```python
from voice_assistant.roles.monitoring import RoleSwitchMetrics

# 獲取切換統計
metrics = RoleSwitchMetrics()
print(f"平均切換時間: {metrics.average_switch_time}ms")
print(f"切換成功率: {metrics.success_rate}%")
```

### Q5: 是否支援角色組合或多重角色？

目前版本不支援角色組合，每個時間點只能有一個活躍角色。未來版本可能考慮此功能。

## 效能調優

### 1. 記憶體優化

- 角色定義使用單例模式，避免重複載入
- 狀態歷史限制為最多 50 條記錄
- 定期清理過期的會話資料

### 2. 響應時間優化

- 角色切換目標時間 < 3 秒
- 意圖識別目標時間 < 500ms
- LLM 請求目標時間 < 2 秒

### 3. 併發處理

- 支援多會話並發角色切換
- 使用異步 I/O 處理 LLM 請求
- 實作角色狀態的原子性操作

## 故障排除

### 常見錯誤

1. **RoleNotFoundError**
   - 檢查角色 ID 是否正確
   - 確認角色是否已註冊

2. **IntentRecognitionError**
   - 檢查 LLM 服務是否正常
   - 驗證輸入文字格式

3. **InvalidRoleSwitchError**
   - 檢查目標角色是否存在
   - 確認當前狀態是否允許切換

### 調試工具

```python
# 啟用詳細日誌
import logging
logging.getLogger("voice_assistant.roles").setLevel(logging.DEBUG)

# 檢視角色狀態
role_state.dump_state()

# 測試意圖識別
recognizer.test_recognition("測試文字")
```

## 下一步

1. **閱讀完整文檔**: 查看完整的 API 文檔和架構說明
2. **擴展角色**: 根據需求開發自定義角色
3. **整合測試**: 在實際應用場景中測試功能
4. **監控優化**: 根據使用數據優化效能

## 支援

如需技術支援或回報問題，請聯繫開發團隊或查看項目 GitHub 頁面。