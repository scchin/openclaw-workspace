# 🛡️ Evidence-Based Clone Research: Consolidation (2026-04-22)

**Source**: `SALVAGED_CONTEXT.md` (v4.x)
**Context**: Integration of specialized macOS cloning research into the core system memory.

## 1. 核心技術共識 (Technical Consensus)

### MacOS 系統層級複製限制
- **SSV (Signed System Volume)**：MacOS Big Sur 及之後版本引入了 SSV 技術，導致傳統的區塊級複製 (`dd`) 無法產生可引導的卷。
- **ASR (Apple Software Restore)**：`sudo asr restore` 是目前唯一獲得官方支持且能處理 SSV 的物理複製路徑。
- **TCC (Transparency, Consent, and Control)**：隱私權限數據庫 (`TCC.db`) 與硬體 UUID 強綁定。克隆後必須手動重置或在停用 SIP 的情況下處理，否則將出現權限失效。
- **Sequoia 卷結構**：啟動卷由五個關鍵卷組成：`SSV`, `Data`, `Preboot`, `Recovery`, `VM`。結構極其複雜，任何單個卷的損毀或缺失均會導致無法啟動。

### 社群實踐建議
- **傾向方向**：主流社群（如 Eclectic Light Co, Bombich）建議採取「文件級備份」而非「鏡像卷複製」，因後者對目標硬體和版本要求過於嚴苛且脆弱。

## 2. 與 `system-clone-local` 的關係
現有的 `system-clone-local` 技能採取的是 **「絕對路徑封裝 (tar -C /)」** 方案。
- **優勢**：避開了 SSV 的區塊級限制，專注於 OpenClaw 應用層與配置層的 1:1 物理還原。
- **差距**：`SALVAGED_CONTEXT` 提供的 ASR 方案屬於「系統級」克隆，而 `system-clone-local` 屬於「應用/配置級」克隆。兩者互補，前者用於全盤遷移，後者用於快速恢復。

## 3. 待執行之任務 (Inherited Tasks)
- [ ] **技術審計**：由備份專家對 ASR 方案與文件級備份方案進行對比審計。
- [ ] **評測會議**：座標化技術評測會議，確定最終克隆方案的權重。
- [ ] **最終提案**：生成一份 100% 可執行的、整合 ASR 與文件級備份的綜合克隆提案。
