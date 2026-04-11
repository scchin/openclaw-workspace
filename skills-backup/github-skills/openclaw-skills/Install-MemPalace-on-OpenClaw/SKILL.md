---
name: Install-MemPalace-on-OpenClaw
description: 從零開始在 OpenClaw 上安裝並整合 MemPalace 長期記憶系統的完整指南。包含下載、安裝、Phase 1/2/3 整合流程、自動化 Hook設定、MCP 設定、以及一鍵搬遷到新機器的完整 SOP。觸發關鍵字：安裝 MemPalace、MemPalace 整合、mempalace 安裝、memcpy、mempalace setup。
author: King Sean of KS
---

# Install-MemPalace-on-OpenClaw

> **完整安裝指南**：從下載到 Phase 3 完全接管，所有流程與關鍵設定。
> 
> **建立日期**：2026-04-11
> **作者**：King Sean of KS
> **適用版本**：MemPalace v3.1.0 + OpenClaw 最新版

---

## 目錄

1. [前置要求](#前置要求)
2. [Phase 0：下載與安裝 MemPalace](#phase-0下載與安裝-mempalace)
3. [Phase 1：MCP Server 整合](#phase-1mcp-server-整合)
4. [Phase 2：雙寫 Hook 整合](#phase-2雙寫-hook-整合)
5. [Phase 3：完全取代舊記憶系統](#phase-3完全取代舊記憶系統)
6. [驗證與測試](#驗證與測試)
7. [一鍵搬遷到新機器](#一鍵搬遷到新機器)
8. [疑難排解](#疑難排解)

---

## 前置要求

### 硬體與軟體

| 項目 | 最低需求 | 建議 |
|------|----------|------|
| Python | 3.13+ | 3.13（ARM64 Mac） |
| pip | 最新版 | `pip3 install --upgrade pip` |
| OpenClaw | 最新版 | v12.x+ |
| 磁碟空間 | 500MB | 2GB（隨著記憶增加） |
| RAM | 4GB | 8GB+ |

### 確認 Python 路徑

```bash
# 確認 Python 3.13 的路徑（必須）
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 --version
# 預期輸出：Python 3.13.x

# 確認 pip 可用
pip3 --version
```

---

## Phase 0：下載與安裝 MemPalace

### Step 0.1：安裝 MemPalace

```bash
pip3 install mempalace
```

**預期輸出：**
```
Successfully installed mempalace-3.1.0
```

### Step 0.2：初始化 Palace 目錄

```bash
# 建立 palace（互動式，需要回答幾個問題）
mempalace

# 或者直接初始化
mempalace init
# 預設路徑：~/.mempalace/
```

**初始化回答：**
```
Palace Name: KingSeanKS
Your Name: KingSeanKS
Save to: /Users/[username]/.mempalace/
```

### Step 0.3：驗證安裝

```bash
python3 - << 'EOF'
import sys
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
import mempalace
print(f"MemPalace version: {mempalace.__version__}")
EOF
```

**預期輸出：**
```
MemPalace version: 3.1.0
```

### Step 0.4：建立設定檔（mempalace.yaml）

```yaml
# ~/.openclaw/workspace/mempalace.yaml
palace:
  path: /Users/[username]/.mempalace
  name: KingSeanKS

wings:
  - name: ks-system
    rooms:
      - knowledge
      - skills
      - decisions
      - general
  
  - name: openclaw-workspace
    rooms:
      - memory
      - skills
      - general
  
  - name: wing_kingseanks
    rooms:
      - diary
```

---

## Phase 1：MCP Server 整合

### Step 1.1：更新 mcporter.json

找到你的 `mcporter.json`：
```bash
# 通常在以下位置之一
~/.openclaw/workspace/config/mcporter.json
~/.openclaw/config/mcporter.json
```

**在 `mcpServers` 區塊新增：**

```json
"mempalace": {
  "command": "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
  "args": ["-m", "mempalace.mcp_server", "--palace", "/Users/[username]/.mempalace"]
}
```

### Step 1.2：完整 mcporter.json 範例

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx @playwright/mcp@latest"
    },
    "filesystem": {
      "command": "node",
      "args": ["/opt/homebrew/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js", "/Users/[username]", "/Users/[username]/.openclaw/workspace"]
    },
    "github": {
      "command": "npx @modelcontextprotocol/server-github@latest",
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "memory": {
      "command": "npx @modelcontextprotocol/server-memory@latest"
    },
    "puppeteer": {
      "command": "npx @modelcontextprotocol/server-puppeteer@latest"
    },
    "mempalace": {
      "command": "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
      "args": ["-m", "mempalace.mcp_server", "--palace", "/Users/[username]/.mempalace"]
    }
  }
}
```

### Step 1.3：重啟 Gateway

```bash
openclaw gateway restart
```

### Step 1.4：驗證 MCP 連線

```bash
python3 - << 'EOF'
import sys
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace import mcp_server

# 測試 status tool
r = mcp_server.handle_request({
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'tools/call',
    'params': {'name': 'mempalace_status', 'arguments': {}}
})
print("✅ mempalace_status:", 'result' in r)

# 測試 search tool
r = mcp_server.handle_request({
    'jsonrpc': '2.0',
    'id': 2,
    'method': 'tools/call',
    'params': {'name': 'mempalace_search', 'arguments': {'query': 'test', 'limit': 3}}
})
print("✅ mempalace_search:", 'result' in r)
EOF
```

**預期輸出：**
```
✅ mempalace_status: True
✅ mempalace_search: True
```

---

## Phase 2：雙寫 Hook 整合

### Step 2.1：建立 Hook 目錄

```bash
mkdir -p ~/.openclaw/hooks/mempalace-memory/
```

### Step 2.2：建立 hook_writer.py

```python
#!/usr/bin/env python3
"""
MemPalace Session Writer — Phase 2 雙寫整合核心
由 OpenClaw Hook 觸發，將 Session 上下文寫入 MemPalace
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_add_drawer, tool_diary_write


def write_session_summary(session_data: dict) -> dict:
    """將 Session 摘要寫入 MemPalace"""
    content = session_data.get("content", "")
    source = session_data.get("source", f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    
    if not content:
        return {"success": False, "error": "No content to write"}
    
    try:
        result = tool_add_drawer(
            content=content,
            wing=session_data.get("wing", "ks-system"),
            room=session_data.get("room", "general"),
            source_file=source
        )
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_diary_entry(entry: str, topic: str = "general", agent: str = "KingSeanKS") -> dict:
    """將日記條目寫入 MemPalace"""
    try:
        result = tool_diary_write(agent_name=agent, entry=entry, topic=topic)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    try:
        input_data = json.loads(sys.stdin.read())
    except Exception:
        print("Usage: echo '{}' | python3 hook_writer.py")
        sys.exit(0)
    
    action = input_data.get("action", "")
    
    if action == "session_summary":
        result = write_session_summary(input_data)
    elif action == "diary":
        result = write_diary_entry(
            entry=input_data.get("entry", ""),
            topic=input_data.get("topic", "general"),
            agent=input_data.get("agent", "KingSeanKS")
        )
    else:
        result = {"success": False, "error": f"Unknown action: {action}"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

### Step 2.3：建立 handler.ts

```typescript
/**
 * MemPalace Memory Hook — Phase 2 雙寫整合
 * 
 * 觸發時機：
 * - session:compact:after  → Session 壓縮完成後，寫入 session summary
 * - gateway:startup       → Gateway 啟動時，讀取 MemPalace 狀態確認
 */

import { existsSync } from "fs";
import { join } from "path";
import { execSync } from "child_process";

const PYTHON = "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3";
const PALACE_PATH = "/Users/[username]/.mempalace";
const LOG_FILE = join(PALACE_PATH, "hook.log");

function log(entry: Record<string, unknown>) {
  try {
    const line = JSON.stringify({ ts: new Date().toISOString(), ...entry });
    execSync(`echo '${line}' >> "${LOG_FILE}"`, { shell: "/bin/zsh" });
  } catch { /* ignore */ }
}

function writeToMemPalace(payload: {
  action: string;
  wing?: string;
  room?: string;
  content?: string;
  source?: string;
  entry?: string;
  topic?: string;
  agent?: string;
}) {
  try {
    const input = JSON.stringify(payload).replace(/'/g, "'\"'\"'");
    const result = execSync(
      `echo '${input}' | ${PYTHON} ~/.openclaw/hooks/mempalace-memory/hook_writer.py`,
      { encoding: "utf8", timeout: 10000 }
    );
    return JSON.parse(result);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    log({ action: "write_failed", error: msg, payload });
    return { success: false, error: msg };
  }
}

export async function onSessionCompactAfter(payload: {
  sessionId: string;
  summary?: string;
  previousHistoryLength?: number;
  newHistoryLength?: number;
  duration?: number;
  messages?: Array<{ role: string; content: string }>;
}) {
  log({ hook: "session:compact:after", payload });

  let summaryContent = payload.summary || "";
  
  if (!summaryContent && payload.messages && payload.messages.length > 0) {
    const recent = payload.messages.slice(-5);
    summaryContent = recent.map((m) => `**${m.role}**: ${m.content.slice(0, 200)}`).join("\n");
  }

  if (summaryContent) {
    const today = new Date().toISOString().split("T")[0];
    writeToMemPalace({
      action: "session_summary",
      wing: "ks-system",
      room: "general",
      content: `## Session Summary — ${today}\n\n${summaryContent}\n\n*Session ID: ${payload.sessionId}*`,
      source: `session-${today}-${payload.sessionId.slice(0, 8)}`
    });

    writeToMemPalace({
      action: "diary",
      entry: `Session ${payload.sessionId.slice(0, 8)} 結束。壓縮後保留 ${payload.newHistoryLength} 條歷史。${summaryContent.slice(0, 100)}...`,
      topic: "session",
      agent: "KingSeanKS"
    });
  }
}

export async function onGatewayStartup() {
  log({ hook: "gateway:startup" });

  const palaceDir = join(PALACE_PATH, "palace");
  if (!existsSync(palaceDir)) {
    log({ action: "palace_not_found", path: palaceDir });
    return;
  }

  writeToMemPalace({
    action: "diary",
    entry: "Gateway 啟動。MemPalace Phase 2 Hook 已就緒。",
    topic: "system",
    agent: "KingSeanKS"
  });

  log({ action: "startup_complete" });
}

export default async function handleHook(event: { type: string; action: string; payload?: unknown }) {
  if (event.type === "session" && event.action === "compact:after") {
    await onSessionCompactAfter(event.payload as Parameters<typeof onSessionCompactAfter>[0]);
  } else if (event.type === "gateway" && event.action === "startup") {
    await onGatewayStartup();
  }
}
```

### Step 2.4：建立 HOOK.json

```json
{
  "name": "mempalace-memory",
  "version": "3.0.0",
  "description": "MemPalace Phase 2 — 雙寫整合 Hook",
  "author": "King Sean of KS",
  "trigger": {
    "session:compact:after": {
      "enabled": true,
      "async": true,
      "handler": "onSessionCompactAfter"
    },
    "gateway:startup": {
      "enabled": true,
      "async": true,
      "handler": "onGatewayStartup"
    }
  },
  "modules": {
    "main": "handler.ts",
    "hook_writer": "hook_writer.py"
  }
}
```

### Step 2.5：建立 CLI 工具 mp

```bash
#!/bin/zsh
# MemPalace CLI wrapper — 快速查詢記憶
# 用法: mp search "關鍵字" 或 mp diary

PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

cmd="${1:-status}"
shift

case "$cmd" in
  s|search)
    query="${*:-test}"
    $PYTHON - << PYEOF
import sys, json
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_search
result = tool_search(query="$query", limit=5)
print(result)
PYEOF
    ;;
  d|diary)
    $PYTHON - << PYEOF
import sys, json
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_diary_read
result = tool_diary_read(agent_name="KingSeanKS", last_n=10)
print(json.dumps(result, indent=2, ensure_ascii=False))
PYEOF
    ;;
  t|taxonomy)
    $PYTHON - << PYEOF
import sys, json
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_get_taxonomy
result = tool_get_taxonomy()
print(json.dumps(result, indent=2, ensure_ascii=False))
PYEOF
    ;;
  *)
    echo "用法: mp [search|diary|taxonomy] [關鍵字...]"
    ;;
esac
```

```bash
chmod +x ~/.openclaw/hooks/mempalace-memory/mp
```

---

## Phase 3：完全取代舊記憶系統

### Step 3.1：遷移 MEMORY.md 到 MemPalace

```python
#!/usr/bin/env python3
"""MEMORY.md 遷移到 MemPalace"""
import sys, re
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_add_drawer

with open('/Users/[username]/.openclaw/workspace/MEMORY.md', 'r') as f:
    content = f.read()

sections = re.split(r'\n(?=## )', content)

for section in sections:
    if not section.strip():
        continue
    
    title_match = re.match(r'## (.+)', section)
    if title_match:
        room = "general"
        title = title_match.group(1)
        
        if "技能" in title:
            room = "skills"
        elif "DISH" in title or "where-to-go" in title:
            room = "skills"
        elif "核心" in title:
            room = "knowledge"
        
        tool_add_drawer(
            content=section.strip(),
            wing="ks-system",
            room=room,
            source_file="MEMORY.md-migration"
        )
        print(f"✅ Migrated: [{room}] {title[:40]}")
```

### Step 3.2：遷移每日日誌

```python
#!/usr/bin/env python3
"""每日日誌遷移到 MemPalace"""
import sys, os
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_add_drawer

memory_dir = '/Users/[username]/.openclaw/workspace/memory/'
files = sorted([f for f in os.listdir(memory_dir) if f.endswith('.md')])

for fname in files:
    fpath = os.path.join(memory_dir, fname)
    with open(fpath, 'r') as f:
        content = f.read()
    
    if not content.strip():
        continue
    
    date = fname.replace('.md', '')
    tool_add_drawer(
        content=content.strip(),
        wing="ks-system",
        room="general",
        source_file=f"daily-memory-{date}"
    )
    print(f"✅ Migrated: {fname}")
```

### Step 3.3：退役 MEMORY.md

將 `MEMORY.md` 內容替換為：

```markdown
# MEMORY.md — 長期記憶（已退役）

> ⚠️ **2026-04-11：此檔案已退役，內容已遷移到 MemPalace**
> 
> 所有記憶現在存在 MemPalace（ChromaDB + SQLite）

---

## 緊急 Fallback（MemPalace 不可用時）

### 核心原則（最高優先）
1. **嚴守分工界線**：未得我明確指示，不得自做主張幫我決定
2. **刪除決定權專屬於用戶**：未得我明確說了，不執行任何刪除

### 技能管理鐵律
- **強制調用** `skill-installation`

### 地點查詢
- **100% 強制使用 `google-places` skill**

---

*此檔案僅保留作為緊急 Fallback。正常流程請使用 MemPalace。*
```

### Step 3.4：建立 wakeup.py（喚醒上下文引擎）

```python
#!/usr/bin/env python3
"""
MemPalace Wake-Up Context Generator — Phase 3 核心引擎
目標：舊制 ~2500 tokens → 新制 ~300 tokens（88% 節省）
"""

import sys
import json
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_search, tool_diary_read, tool_status


def get_compact_context(topic: str = "King Sean of KS", limit: int = 5) -> str:
    lines = ["## 📜 MemPalace Wake-Up Context"]

    try:
        r = tool_status()
        drawers = r.get('total_drawers', '?')
        lines.append(f"- 🏛️ Palace: {drawers} drawers active")
    except:
        lines.append("- 🏛️ Palace: active")

    try:
        r = tool_diary_read(agent_name="KingSeanKS", last_n=2)
        entries = r.get('entries', [])
        if entries:
            lines.append("- 📅 最近:")
            for e in entries[-2:]:
                content = e.get('content', '')[:70]
                lines.append(f"  • {e.get('date')} {content}...")
    except:
        pass

    try:
        r = tool_search(query="核心原則 霸王條款 分工界線", limit=1)
        results = r.get('results', [])
        if results:
            text = results[0].get('text', '')[:100].replace('\n', ' ')
            lines.append(f"- ⚠️ 原則: {text}...")
    except:
        pass

    lines.append("---")
    lines.append("*更多請用 `mp search \"關鍵字\"` 查詢 MemPalace*")

    return "\n".join(lines)


if __name__ == "__main__":
    print(get_compact_context())
```

### Step 3.5：建立技能 mempalace/SKILL.md

```markdown
---
name: mempalace
description: MemPalace 長期記憶系統。觸發關鍵字：搜尋記憶、查歷史、MemPalace、記得我之前說過。
author: King Sean of KS
---

# MemPalace — AI 記憶宮殿 Phase 3

## 架構

- **Wings**: ks-system / openclaw-workspace / wing_kingseanks
- **Rooms**: knowledge / skills / decisions / general / memory / diary

## 工具

| 工具 | 用途 |
|------|------|
| `mempalace_search` | 語意搜尋 |
| `mempalace_diary_read` | 讀取日記 |
| `mempalace_add_drawer` | 寫入記憶 |
| `mempalace_status` | 查看狀態 |

## CLI

```bash
mp search "關鍵字"
mp diary
```
```

---

## 驗證與測試

### 測試指令

```bash
# 1. MCP 工具測試
python3 - << 'EOF'
import sys
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace import mcp_server

tools = [
    'mempalace_status',
    'mempalace_search',
    'mempalace_diary_read',
    'mempalace_diary_write',
    'mempalace_kg_stats',
    'mempalace_kg_query',
    'mempalace_check_duplicate',
    'mempalace_list_wings',
    'mempalace_list_rooms',
]

for name in tools:
    r = mcp_server.handle_request({
        'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': name, 'arguments': {}}
    })
    ok = 'result' in r or 'content' in r
    print(f"{'✅' if ok else '❌'} {name}")
EOF

# 2. CLI 測試
mp search "核心原則"
mp diary

# 3. Wake-up 測試
python3 ~/.openclaw/hooks/mempalace-memory/wakeup.py
```

### 效率對比

| 維度 | 舊制 | 新制 |
|------|------|------|
| Session 啟動 Token | ~1,406 | ~85 |
| Token 節省 | — | **94%** |
| 搜尋方式 | 讀檔案 | 語意搜尋 |
| 歷史理解 | 無 | 自動上下文 |

---

## 一鍵搬遷到新機器

### 自動安裝腳本（install_mempalace.sh）

```bash
#!/bin/zsh
# MemPalace 一鍵安裝腳本
# 用法: curl -fsSL [URL] | zsh

set -e

echo "═══ MemPalace × OpenClaw 一鍵安裝 ═══"
echo ""

# 1. 安裝 MemPalace
echo "【1/6】安裝 MemPalace..."
pip3 install mempalace

# 2. 初始化
echo "【2/6】初始化 Palace..."
mkdir -p ~/.mempalace
mempalace init --path ~/.mempalace --name KingSeanKS --agent KingSeanKS

# 3. 建立設定檔
echo "【3/6】建立 mempalace.yaml..."
cat > ~/.openclaw/workspace/mempalace.yaml << 'YAML'
palace:
  path: ~/.mempalace
  name: KingSeanKS
wings:
  - name: ks-system
    rooms: [knowledge, skills, decisions, general]
  - name: openclaw-workspace
    rooms: [memory, skills, general]
  - name: wing_kingseanks
    rooms: [diary]
YAML

# 4. 更新 mcporter.json
echo "【4/6】更新 mcporter.json..."
# ...（完整腳本見下方）

# 5. 建立 Hook
echo "【5/6】建立 Hook..."
mkdir -p ~/.openclaw/hooks/mempalace-memory/
# ...（複製 hook_writer.py, handler.ts, wakeup.py）

# 6. 建立 CLI
echo "【6/6】建立 CLI 工具..."
# ...（建立 mp script）

echo ""
echo "═══ 安裝完成 ═══"
echo "請重啟 Gateway: openclaw gateway restart"
```

### 完整還原流程

```bash
# Step 1: 安裝 MemPalace
pip3 install mempalace

# Step 2: 從 GitHub 還原技能
cd ~/.openclaw/skills
git clone https://github.com/[your-repo]/openclaw-workspace.git .

# Step 3: 還原 Palace 資料（如果有備份）
# cp -r backup/.mempalace ~/

# Step 4: 重啟 Gateway
openclaw gateway restart

# Step 5: 驗證
mp status
python3 ~/.openclaw/hooks/mempalace-memory/wakeup.py
```

---

## 疑難排解

### MemPalace 安裝失敗

```bash
# 確認 Python 版本
python3 --version  # 必須 3.13+

# 強制安裝
pip3 install --force-reinstall mempalace

# 手動安裝依賴
pip3 install chromadb fastapi typer uvicorn
```

### MCP Server 無法啟動

```bash
# 檢查 Python 路徑
which python3
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3

# 測試直接啟動
python3 -m mempalace.mcp_server --palace ~/.mempalace

# 檢查 mcporter.json 語法
python3 -c "import json; json.load(open('~/.openclaw/workspace/config/mcporter.json'))"
```

### Hook 無法寫入

```bash
# 檢查權限
ls -la ~/.openclaw/hooks/mempalace-memory/

# 手動測試 hook_writer.py
echo '{"action": "diary", "entry": "test", "topic": "system"}' | python3 ~/.openclaw/hooks/mempalace-memory/hook_writer.py
```

### ChromaDB Segfault（ARM64 Mac）

```bash
# 重建索引
mempalace repair

# 或刪除後重建
rm -rf ~/.mempalace/chroma/
mempalace init
```

---

## 關鍵時間戳

| 事件 | 日期 | 備註 |
|------|------|------|
| MemPalace 安裝 | 2026-04-11 | pip install mempalace v3.1.0 |
| Phase 1 完成 | 2026-04-11 | MCP Server 整合 |
| Phase 2 完成 | 2026-04-11 | Hook 雙寫系統 |
| Phase 3 完成 | 2026-04-11 | 完全取代舊記憶 |
| MEMORY.md 退役 | 2026-04-11 | 內容遷移到 MemPalace |
| 技能建立 | 2026-04-11 | Install-MemPalace-on-OpenClaw v1.0 |

---

## 相關技能

| 技能 | 用途 |
|------|------|
| `mempalace` | MemPalace 長期記憶系統（本體） |
| `skill-installation` | 技能安裝/診斷/修復 |
| `skills-github-backup` | 備份與還原技能至 GitHub |
