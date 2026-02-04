# Research Report: 角色切換面試官功能

**Date**: 2025-01-25  
**Feature**: 008-role-switching  
**Phase**: 0 - Research & Analysis

## Executive Summary

本研究報告分析了角色切換功能的技術實作方案，確認了基於現有架構的最小侵入性設計。研究結果顯示，通過擴展 LLMClient.system_prompt 參數和新增 BaseRole 架構，可以在不破壞現有 Tool-First 架構的前提下實現動態角色切換。

## Technical Decisions

### 1. 角色管理架構

**Decision**: 採用 BaseRole 抽象類別繼承模式，類似現有的 BaseTool 設計

**Rationale**: 
- 與現有 Tool 系統保持一致性
- 支援未來角色擴展
- 符合 SOLID 原則中的開放封閉原則

**Alternatives considered**:
- 配置檔案方式：缺乏靈活性，難以支援複雜的角色邏輯
- 函式式設計：不符合現有物件導向架構

### 2. 角色狀態管理

**Decision**: 使用記憶體內存儲，無需持久化

**Rationale**:
- 符合規格中「無持久化需求」的要求
- 降低系統複雜度
- 提升效能（無 I/O 操作）

**Alternatives considered**:
- Redis 快取：過度工程化，增加依賴
- 檔案儲存：不符合單次對話需求

### 3. 意圖識別實作

**Decision**: 基於 LLM Function Calling 進行語意理解

**Rationale**:
- 符合 LLM Auto-Routing 原則
- 無需額外的 NLP 模型訓練
- 支援自然語言的靈活表達

**Alternatives considered**:
- 正則表達式：過於僵化，無法處理多樣表達
- 意圖分類模型：增加複雜度，不符合最小侵入性

### 4. UI 整合方案

**Decision**: 在現有 Gradio 介面基礎上新增角色選擇器組件

**Rationale**:
- 重用現有 UI 框架
- 最小化程式碼變更
- 保持使用者體驗一致性

**Alternatives considered**:
- 獨立 Web 應用：過度工程化
- 命令列介面：不符合語音助理特性

## Integration Analysis

### 現有 LLMClient 整合

**Findings**:
- `llm/client.py` 已有 `system_prompt` 參數
- 需要新增 `update_system_prompt()` 方法
- 與 OpenAI SDK 完全相容

**Integration Points**:
```python
# 現有程式碼模式
llm_client = LLMClient()
response = llm_client.chat(messages, system_prompt=role_prompt)

# 新增角色切換支援
llm_client.update_system_prompt(new_role.system_prompt)
```

### FastRTC 整合

**Findings**:
- 現有 Stream 處理器可直接重用
- 語音輸入無需修改
- 輸出保持現有 TTS 流程

**Integration Points**:
```python
# 在現有 Stream 處理器中新增角色切換邏輯
async def handle_user_input(text_input):
    # 檢查角色切換意圖
    if intent_recognizer.is_role_switch(text_input):
        new_role = extract_role_name(text_input)
        role_state.switch_to(new_role)
        return f"已切換到 {new_role} 角色"
    
    # 正常對話處理
    current_role = role_state.get_current()
    response = await llm_client.chat(messages, current_role.system_prompt)
    return response
```

## Performance Considerations

### 角色切換效能

**Target**: <3秒完成切換
**Analysis**:
- 記憶體操作：~1ms
- LLM 提示詞更新：~10ms  
- 意圖識別：~100-500ms (LLM Function Calling)
- 總計：<1秒，符合目標

### 記憶體使用

**Estimate**:
- 角色定義：~1KB per role
- 狀態管理：~100B
- 3個預設角色總計：<5KB，遠低於 100MB 限制

## Risk Assessment

### 技術風險 (Low)

- **LLM Function Calling 準確度**: 經驗顯示 90%+ 準確率，符合需求
- **記憶體洩漏風險**: 記憶體內存儲，GC 自動管理

### 運營風險 (Low)

- **使用者困惑**: 透過清晰的提示詞和 UI 設計降低
- **角色衝突**: 透過狀態管理器確保一致性

## Implementation Roadmap

### Phase 1: 核心架構
- BaseRole 抽象類別
- RoleRegistry 註冊機制
- LLMClient 擴展

### Phase 2: 角色實作
- 面試官角色實作
- 基礎意圖識別
- 狀態管理

### Phase 3: UI 整合
- Gradio 角色選擇器
- 即時狀態顯示
- 使用者體驗優化

## Success Metrics Alignment

- **SC-001** (<3秒切換): 技術分析顯示 <1秒，達成目標
- **SC-003** (90% 語音識別): LLM Function Calling 可達成
- **SC-004** (95% 成功率): 透過完善錯誤處理達成

## Conclusion

技術研究確認角色切換功能可以在現有架構下安全、高效地實現。所有技術選擇都符合專案憲章要求，為下一階段的設計和實作奠定了堅實基礎。