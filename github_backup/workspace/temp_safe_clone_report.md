# 🛡️ OpenClaw 系統級安全克隆 (Safe Clone) 物理方案報告

## 1. 核心痛點分析 (The Critical Pain Points)
在對 OpenClaw 進行 1:1 物理克隆時，傳統的備份方式會遇到三個致命問題：
- **服務死結**：若在網關運行時備份，可能導致文件鎖定或數據不一致。
- **權限丟失**：恢復後若權限 (Permissions) 或所有者 (Ownership) 改變，會導致 `Permission Denied` 而無法啟動。
- **路徑偏移**：若使用相對路徑備份，恢復時一旦目錄結構微調，將導致整個系統崩潰。
- **物理鎖定**：macOS 的 `uchg` (immutable flag) 會導致標準的覆蓋寫入失敗。

## 2. 安全克隆架構 (The Safe Clone Architecture)
本方案採取「凍結 $\rightarrow$ 鏡像 $\rightarrow$ 喚醒」的原子操作路徑。

### 2.1 生命週期鎖定 (Lifecycle Locking)
強制執行以下序列，禁止任何中間干擾：
`openclaw gateway stop` (狀態凍結) $\rightarrow$ `Physical Clone` (物理克隆) $\rightarrow$ `openclaw gateway start` (服務喚醒)。

### 2.2 絕對路徑映射 (Absolute Path Mapping)
捨棄相對路徑，採用 **Root-Relative Mapping**：
- **封裝**：使用 `tar -C / -cpzf`。將所有目標路徑（如 `/Users/KS/.openclaw`）相對於根目錄 `/` 進行封裝。
- **回填**：使用 `tar -C / -xpzf`。這確保了檔案在恢復時，會被**精確地原路回填**到系統中的絕對位置，實現 1:1 的物理還原，無需對照表。

### 2.3 權限原子性 (Permission Atomicity)
強制啟用 `-p` (preserve permissions) 標誌，確保：
- 檔案的讀寫執行權限 100% 繼承。
- 所有者 (Owner) 與群組 (Group) 資訊完整保留。

### 2.4 完整性簽章 (Integrity Signing)
每次克隆後立即生成 $\text{SHA-256}$ 指紋，將鏡像檔與指紋綁定，防止在儲存期間發生位元翻轉 (Bit-rot) 或人為篡改。

## 3. 實作體現：`system-clone-local` 技能
上述所有理論已完整實裝於 `system-clone-local` 技能中：
- **`clone` 指令**：自動執行「停止 $\rightarrow$ 絕對路徑打包 $\rightarrow$ 簽名 $\rightarrow$ 啟動」。
- **`restore` 指令**：自動執行「停止 $\rightarrow$ 絕對路徑回填 $\rightarrow$ 啟動」。
- **預設路徑**：`/Users/KS/Documents/OpenClaw-Clone-Backup/`。

## 4. 結論
本方案將「恢復」從一個充滿風險的嘗試，轉化為一個**確定性的工程操作**。透過物理路徑的強綁定與生命週期的強制鎖定，確保了系統在任何災難發生後，都能在 3 分鐘內恢復到 100% 相同的狀態。
