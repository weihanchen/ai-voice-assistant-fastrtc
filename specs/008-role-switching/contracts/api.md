# Role Management API Specification

**Version**: 1.0.0  
**Date**: 2025-01-25  
**Feature**: 008-role-switching

## Overview

本文件定義了角色管理系統的內部 API 契約，用於角色註冊、切換、查詢等操作。這些 API 主要為內部系統呼叫，不對外暴露。

## API Endpoints

### 1. 角色管理

#### 1.1 註冊新角色

```http
POST /internal/api/roles
Content-Type: application/json

{
  "id": "custom-role",
  "name": "自定義角色",
  "role_type": "custom",
  "system_prompt": "你是一個自定義角色...",
  "tone_style": "友善、專業",
  "description": "自定義角色描述",
  "example_responses": ["範例回應1", "範例回應2"]
}
```

**Success Response (201)**:
```json
{
  "success": true,
  "data": {
    "id": "custom-role",
    "name": "自定義角色",
    "role_type": "custom",
    "system_prompt": "你是一個自定義角色...",
    "tone_style": "友善、專業",
    "description": "自定義角色描述",
    "example_responses": ["範例回應1", "範例回應2"],
    "is_active": true,
    "created_at": "2025-01-25T10:00:00Z",
    "updated_at": null
  }
}
```

**Error Response (400)**:
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "角色 ID 已存在",
    "field": "id",
    "timestamp": "2025-01-25T10:00:00Z"
  }
}
```

#### 1.2 獲取角色列表

```http
GET /internal/api/roles
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "roles": [
      {
        "id": "interviewer",
        "name": "面試官",
        "role_type": "interviewer",
        "tone_style": "正式、專業",
        "description": "專業面試官角色",
        "is_active": true
      }
    ],
    "total": 3
  }
}
```

#### 1.3 獲取特定角色

```http
GET /internal/api/roles/{role_id}
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "id": "interviewer",
    "name": "面試官",
    "role_type": "interviewer",
    "system_prompt": "你是一位專業的面試官...",
    "tone_style": "正式、專業",
    "description": "專業面試官角色",
    "example_responses": ["可以請您詳細說明一下嗎？"],
    "is_active": true,
    "created_at": "2025-01-25T10:00:00Z",
    "updated_at": null
  }
}
```

**Error Response (404)**:
```json
{
  "success": false,
  "error": {
    "type": "RoleNotFoundError",
    "message": "角色 'unknown-role' 不存在",
    "role_id": "unknown-role",
    "timestamp": "2025-01-25T10:00:00Z"
  }
}
```

### 2. 角色狀態管理

#### 2.1 切換角色

```http
POST /internal/api/role-state/switch
Content-Type: application/json

{
  "session_id": "session-123",
  "target_role_id": "interviewer",
  "reason": "user_voice_command"
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "session_id": "session-123",
    "current_role_id": "interviewer",
    "previous_role_id": "assistant",
    "switch_time": "2025-01-25T10:00:00Z",
    "confirmation_message": "已切換到面試官角色"
  }
}
```

**Error Response (400)**:
```json
{
  "success": false,
  "error": {
    "type": "InvalidRoleSwitchError",
    "message": "無效的角色切換",
    "target_role_id": "invalid-role",
    "timestamp": "2025-01-25T10:00:00Z"
  }
}
```

#### 2.2 獲取當前角色狀態

```http
GET /internal/api/role-state/{session_id}
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "session_id": "session-123",
    "current_role": {
      "id": "interviewer",
      "name": "面試官",
      "role_type": "interviewer"
    },
    "last_updated": "2025-01-25T10:00:00Z",
    "transition_count": 3
  }
}
```

#### 2.3 獲取角色切換歷史

```http
GET /internal/api/role-state/{session_id}/history?limit=10
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "session_id": "session-123",
    "history": [
      {
        "from_role": "assistant",
        "to_role": "interviewer",
        "reason": "user_voice_command",
        "timestamp": "2025-01-25T10:00:00Z"
      }
    ],
    "total": 3,
    "limit": 10
  }
}
```

### 3. 意圖識別

#### 3.1 識別用戶意圖

```http
POST /internal/api/intent/recognize
Content-Type: application/json

{
  "text": "請切換到面試官",
  "session_id": "session-123"
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "intent_type": "role_switch",
    "confidence": 0.95,
    "target_role": "interviewer",
    "original_text": "請切換到面試官",
    "processing_time_ms": 150
  }
}
```

**Error Response (500)**:
```json
{
  "success": false,
  "error": {
    "type": "IntentRecognitionError",
    "message": "意圖識別失敗",
    "original_text": "請切換到面試官",
    "timestamp": "2025-01-25T10:00:00Z"
  }
}
```

### 4. UI 狀態同步

#### 4.1 獲取 UI 所需的完整狀態

```http
GET /internal/api/ui/role-state/{session_id}
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "current_role": {
      "id": "interviewer",
      "name": "面試官",
      "description": "專業面試官角色"
    },
    "available_roles": [
      {
        "id": "interviewer",
        "name": "面試官",
        "description": "專業面試官角色",
        "is_active": true
      },
      {
        "id": "assistant",
        "name": "助理",
        "description": "一般助理角色",
        "is_active": true
      }
    ],
    "last_switch_time": "2025-01-25T10:00:00Z",
    "total_switches": 3
  }
}
```

## Data Schemas

### Base Response Structure

所有 API 回應都遵循統一結構：

```typescript
interface SuccessResponse<T> {
  success: true;
  data: T;
}

interface ErrorResponse {
  success: false;
  error: {
    type: string;
    message: string;
    [key: string]: any;
    timestamp: string;
  };
}
```

### Error Types

| 錯誤類型 | HTTP 狀態碼 | 描述 |
|---------|------------|------|
| ValidationError | 400 | 請求參數驗證失敗 |
| RoleNotFoundError | 404 | 角色不存在 |
| InvalidRoleSwitchError | 400 | 無效的角色切換 |
| RoleRegistrationLimitError | 429 | 角色註冊數量達到上限 |
| IntentRecognitionError | 500 | 意圖識別失敗 |
| InternalServerError | 500 | 內部伺服器錯誤 |

## Rate Limiting

- **角色註冊**: 10 requests/minute
- **角色切換**: 60 requests/minute
- **意圖識別**: 100 requests/minute
- **狀態查詢**: 200 requests/minute

## Authentication

所有 API 都需要內部認證，使用 session-based 認證機制：

```http
Authorization: Bearer {session_token}
X-Session-ID: {session_id}
```

## Security Considerations

1. **輸入驗證**: 所有輸入都必須經過嚴格驗證
2. **輸出過濾**: 敏感資訊不得暴露在回應中
3. **會話隔離**: 不同會話的資料完全隔離
4. **錯誤處理**: 錯誤訊息不得洩露系統內部資訊

## Performance Requirements

- **回應時間**: 95% 的請求 < 100ms
- **併發支援**: 支援 100+ 並發請求
- **記憶體使用**: 單會話 < 1MB

## Monitoring & Logging

### 關鍵指標

1. **角色切換成功率**: > 99%
2. **意圖識別準確率**: > 90%
3. **平均回應時間**: < 50ms
4. **錯誤率**: < 1%

### 日誌格式

```json
{
  "timestamp": "2025-01-25T10:00:00Z",
  "level": "INFO",
  "session_id": "session-123",
  "api_endpoint": "/internal/api/role-state/switch",
  "method": "POST",
  "duration_ms": 45,
  "status_code": 200,
  "user_agent": "Internal/1.0",
  "extra": {
    "target_role": "interviewer",
    "reason": "user_voice_command"
  }
}
```

## Testing Strategy

### 單元測試

- 每個 API 端點都有對應的單元測試
- 測試覆蓋率 > 90%
- 包含正常和異常情況測試

### 整合測試

- API 串接測試
- 資料流測試
- 效能測試

### 契約測試

- 使用 OpenAPI 規範進行契約測試
- 確保 API 介面穩定性

## Versioning

API 版本採用語義化版本控制：
- **主版本**: 不相容的 API 變更
- **次版本**: 向後相容的新功能
- **修訂版本**: 向後相容的問題修復

當前版本：v1.0.0