---
name: commit
description: 執行提交前檢查（linting、測試、code review）並建立 git commit。當使用者說「commit」、「提交」、「幫我提交」時使用。
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# Git Commit Skill

建立 Git commit 前執行完整的檢查流程。

## 執行流程

### 階段 1：程式碼品質檢查

1. **Ruff Linting**
   - 執行 `uv run ruff check src/`
   - 若有錯誤，先修復再繼續

2. **Ruff Format**
   - 執行 `uv run ruff format src/`
   - 確保程式碼格式符合規範

3. **執行測試**
   - 執行 `uv run pytest tests/ -v --tb=short`
   - 若測試失敗，停止流程並報告

### 階段 2：Code Review

4. **檢視變更內容**
   - 執行 `git diff --stat` 了解變更範圍
   - 執行 `git diff` 詳細檢視變更

5. **Code Review 檢查清單**
   針對每個變更的檔案，檢查：

   **基本檢查**：
   - [ ] 程式碼邏輯是否正確
   - [ ] 是否有潛在的 bug 或邊界情況未處理
   - [ ] 是否有安全性問題（如 SQL injection、XSS、硬編碼密碼等）
   - [ ] 命名是否清晰、符合專案慣例
   - [ ] 是否有遺漏的 logging 或過多的 logging

   **設計原則**：
   - [ ] **KISS & YAGNI**：是否過度設計？是否只解決當前需求？
   - [ ] **DRY**：是否有重複邏輯可抽取？
   - [ ] **防禦性程式設計**：Null Check、Exception Handling 是否完整？

   **效能考量**：
   - [ ] 是否有不必要的資源開銷（記憶體、連線池、I/O）？
   - [ ] 演算法複雜度是否合理？

   **SOLID 原則檢查**：
   - [ ] **S - 單一職責原則 (SRP)**：每個 class/function 是否只負責一件事？
   - [ ] **O - 開放封閉原則 (OCP)**：是否對擴展開放、對修改封閉？新增功能時是否不需要修改現有程式碼？
   - [ ] **L - 里氏替換原則 (LSP)**：子類別是否能完全替換父類別使用？繼承關係是否合理？
   - [ ] **I - 介面隔離原則 (ISP)**：介面是否過於龐大？是否應該拆分成更小的介面？
   - [ ] **D - 依賴反轉原則 (DIP)**：高階模組是否依賴抽象而非具體實作？是否使用依賴注入？

6. **若發現問題**
   - 列出問題清單
   - 詢問使用者是否要修復後再提交

### 階段 3：準備 Commit

7. **查看 Git 狀態**
   - 執行 `git status` 確認要提交的檔案
   - 執行 `git log --oneline -5` 了解 commit message 風格

8. **建立 Commit**
   - 將相關檔案加入暫存區
   - 根據變更內容撰寫 commit message
   - 遵循專案的 commit message 風格
   - 使用 HEREDOC 格式確保訊息格式正確

## Commit Message 格式

```
<type>: <簡短描述>

<詳細說明（若需要）>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

**Type 類型**：
- `feat`: 新功能
- `fix`: Bug 修復
- `refactor`: 重構（不改變功能）
- `docs`: 文件更新
- `test`: 測試相關
- `chore`: 雜項（設定、建置等）
- `perf`: 效能優化

## 完成後回報

### ✅ 檢查結果
- [ ] Ruff linting 通過
- [ ] Ruff format 通過
- [ ] 測試通過
- [ ] Code Review 完成（無問題 / 已修復）

### 📝 Commit 資訊
- Commit hash: （提交後顯示）
- 變更檔案數:
- 變更摘要:

## 注意事項

- 不要執行 `git push`，除非使用者明確要求
- 若有未追蹤的重要檔案，詢問是否要加入
- 若使用者提供額外說明，可作為 commit message 的參考
