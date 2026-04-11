---
name: chinese-date
description: 中國農民曆查詢工具。即時查詢任意西元日期的完整農民曆資訊，包含：四柱干支（年/月/日/時）、生肖、二十四節氣、農曆日期、黃曆宜忌。使用 cantian-tymext 專業命理引擎驅動干支計算，精確可靠。觸發場景：「今天農曆幾號」、「查干支」、「黃曆宜忌」、「節氣」、「八字查詢」。
author: King Sean of KS
---

# 中國日期查詢（chinese-date）

即時查詢任意西元日期的完整農民曆資訊。

## 使用方式

### 查詢今天（使用系統當前時間）

```bash
/usr/local/bin/python3 /Users/KS/.openclaw/skills/chinese-date/scripts/date_query.py
```

### 指定日期時間

```bash
# 參數：年 月 日 [時 [分]]
# 不給時分 → 預設使用系統當前時間

/usr/local/bin/python3 /Users/KS/.openclaw/skills/chinese-date/scripts/date_query.py 2026 3 20    # 查 2026-03-20 系統時間
/usr/local/bin/python3 /Users/KS/.openclaw/skills/chinese-date/scripts/date_query.py 2026 3 20 0 54  # 凌晨
/usr/local/bin/python3 /Users/KS/.openclaw/skills/chinese-date/scripts/date_query.py 2026 2 17 12 0  # 春節中午
/usr/local/bin/python3 /Users/KS/.openclaw/skills/chinese-date/scripts/date_query.py 2026 1 1 12 0   # 元旦中午
```

### 便捷 shell wrapper（自動找 Python3）

```bash
bash /Users/KS/.openclaw/skills/chinese-date/scripts/query.sh 2026 3 20 0 54
```

## 輸出範例

```
================================================
  📅 西元：2026 年 3 月 20 日  星期五
  🎯 干支：丙午 年 / 辛卯 月 / 癸巳 日 / 壬子 時
  🐾 生肖：馬 年
  🌿 節氣：春分
  📆 農曆：丙午年辛卯月癸巳日
  ✅ 宜：出行、嫁娶、掃墓、掃舍、整手足甲、求醫、沐浴
  ❌ 忌：伐木、動土、吵架、安葬、破土、遠行、開市
================================================
```

## 首次安裝

在新電腦上執行懶人安裝腳本：

```bash
bash /Users/KS/.openclaw/skills/chinese-date/scripts/install.sh
```

或手動一行一行安裝：

```bash
# 1. 安裝命理引擎
npm install -g cantian-tymext

# 2. 無需額外 Python 套件（v3 起已內建所有計算）
```

## 架構

```
chinese-date/
├── SKILL.md              ← 本文件
├── scripts/
│   ├── install.sh        ← 懶人安裝腳本（首次設定用）
│   ├── query.sh          ← 便捷 shell wrapper
│   └── date_query.py     ← 主程式（v3，2026-03-31）
```

### 依賴

| 套件 | 安裝方式 | 用途 |
|------|---------|------|
| `cantian-tymext` | `npm install -g cantian-tymext` | 四柱干支、二十四節氣、黃曆宜忌、二十八宿等（基於 tyme4ts） |
| Python 3 | 系統已有 | subprocess 調用 Node.js、輸出格式化 |

### 為何用 Node.js + Python 混合？

- `cantian-tymext` 基於 `tyme4ts`，是現今最精確的八字/干支排盤引擎，支援完整的四柱、月建、節氣、黃曆宜忌、二十八宿等計算
- Python 負責 subprocess 調用 Node.js、日期時間處理、輸出格式化

## 精確度驗證

| 測試時間 | 年柱 | 月柱 | 日柱 | 時柱 | 生肖 | 節氣 |
|---------|------|------|------|------|------|------|
| 2026-03-20 00:54 | 丙午 ✅ | 辛卯 ✅ | 癸巳 ✅ | 壬子 ✅ | 馬 ✅ | 春分 ✅ |
| 2026-03-20 01:08 | 丙午 ✅ | 辛卯 ✅ | 癸巳 ✅ | 癸丑 ✅ | 馬 ✅ | 春分 ✅ |
| 2026-03-20 12:00 | 丙午 ✅ | 辛卯 ✅ | 癸巳 ✅ | 戊午 ✅ | 馬 ✅ | 春分 ✅ |

## 限制

- 節氣日期每年可能有 1-2 天誤差（使用固定日期表，精確需用天文算法）
- cantian-tymext 支援 1900–2100 年
- 黃曆宜忌為習俗參考，非精確曆法計算
