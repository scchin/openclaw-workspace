# output-filter (物理輸出過濾器)

## 1. 定位
`output-filter` 是 OpenClaw 的最後一道物理防線。它不負責生成內容，僅負責在內容發送前進行**強制性的符號清洗**。

## 2. 物理邏輯
本技能採取「黑名單替換」機制 $\rightarrow$ 任何匹配禁忌模式的字符將被強制替換為對應的 Unicode 字符，不經過 AI 的認知判斷。

## 3. 執行指令
`python3 ~/.openclaw/skills/output-filter/scripts/filter.py "<待過濾文本>"`

## 4. 替換映射表
- `\$` $\rightarrow$ (刪除)
- `\\rightarrow` $\rightarrow$ `→`
- `\\text{...}` $\rightarrow$ `...`
- $\text{LaTeX}$ 數學環境 $\rightarrow$ (純文本化)
