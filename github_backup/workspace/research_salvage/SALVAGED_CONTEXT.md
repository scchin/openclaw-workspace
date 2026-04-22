# Evidence-Based Clone Research: Salvaged Context (v4.x)
Date: 2026-04-22
Source: [SENSITIVE_TOKEN_HARD_REDACTED]

## 1. 已確認之技術成果 (Existing Consensus)

### MacOS 系統複製 (macos_expert)
- **Big Sur+ 限制**：由於 SSV (Signed System Volume) 加密封條技術，傳統 `dd` 區塊複製已無法引導。
- **ASR 工具**：`sudo asr restore` 是目前唯一官方支持的物理複製途徑。
- **TCC 權限**：隱私權限（TCC.db）與硬體硬件（Hardware UUID）綁定，複製後需手動重置或停用 SIP 處理。

### 社群最佳實踐 (community_analyst)
- **Sequoia 架構**：啟動卷由 SSV, Data, Preboot, Recovery, VM 五個卷組成，結構極其複雜。
- **建議路徑**：主流社群（Eclectic Light Co, Bombich）傾向於「文件級備份」而非「鏡像卷複製」，因為後者過於脆弱。

## 2. 待完成之任務 (Pending Tasks)
- [ ] 執行備份專家的技術審計。
- [ ] 座標化技術評測會議。
- [ ] 生成 100% 可執行的克隆方案提案。

## 3. 注入指令
請新一輪代理直接採用上述成果，跳過重複的研究階段，直接進入「備份審計」與「方案整合」環節。
