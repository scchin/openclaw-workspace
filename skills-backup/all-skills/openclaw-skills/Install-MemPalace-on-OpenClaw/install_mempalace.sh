#!/bin/zsh
# =============================================================================
# MemPalace × OpenClaw 一鍵安裝腳本
# =============================================================================
# 用法:
#   curl -fsSL [URL] | zsh
#   或下載後直接執行: zsh install_mempalace.sh
#
# 作者: King Sean of KS
# 日期: 2026-04-11
# 版本: 1.0
# =============================================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  MemPalace × OpenClaw 一鍵安裝                               ║"
echo "║  King Sean of KS — 2026-04-11                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# 顏色定義
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo "${GREEN}[OK]${NC}   $1"; }
log_warn()  { echo "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# 參數取得
# =============================================================================
USERNAME=$(whoami)
HOME_DIR=$(eval echo ~)
PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
PALACE_PATH="$HOME_DIR/.mempalace"
OPENCLAW_PATH="$HOME_DIR/.openclaw"
SKILLS_PATH="$OPENCLAW_PATH/skills"
HOOK_PATH="$OPENCLAW_PATH/hooks/mempalace-memory"
MCPORTER_PATH="$OPENCLAW_PATH/workspace/config/mcporter.json"

# =============================================================================
# Step 0: 環境檢查
# =============================================================================
echo ""
echo "【Step 0】環境檢查"
echo "─────────────────────────────────────────"

# 檢查 Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    log_ok "Python: $PYTHON_VERSION"
else
    log_error "Python3 未安裝"
    exit 1
fi

# 檢查 pip
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version 2>&1 | awk '{print $2}')
    log_ok "pip: $PIP_VERSION"
else
    log_error "pip3 未安裝"
    exit 1
fi

# 檢查 OpenClaw
if [ -d "$OPENCLAW_PATH" ]; then
    log_ok "OpenClaw: $OPENCLAW_PATH"
else
    log_error "OpenClaw 目錄不存在: $OPENCLAW_PATH"
    exit 1
fi

# 確認 Python 3.13
PYTHON_313=$(/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 --version 2>&1 || echo "NOT_FOUND")
if [[ "$PYTHON_313" == "Python 3.13"* ]]; then
    log_ok "Python 3.13: $PYTHON_313"
else
    log_warn "Python 3.13 未找到，使用系統 Python3"
    PYTHON_PATH=$(which python3)
fi

# =============================================================================
# Step 1: 安裝 MemPalace
# =============================================================================
echo ""
echo "【Step 1/7】安裝 MemPalace"
echo "─────────────────────────────────────────"

log_info "執行: pip3 install mempalace"
pip3 install mempalace --quiet
log_ok "MemPalace 安裝完成"

# 驗證
MEMPALACE_VERSION=$(python3 -c "import mempalace; print(mempalace.__version__)" 2>&1 || echo "ERROR")
if [[ "$MEMPALACE_VERSION" == "3.1.0" ]]; then
    log_ok "MemPalace 版本: $MEMPALACE_VERSION"
else
    log_error "MemPalace 版本驗證失敗"
    exit 1
fi

# =============================================================================
# Step 2: 初始化 Palace
# =============================================================================
echo ""
echo "【Step 2/7】初始化 Palace"
echo "─────────────────────────────────────────"

log_info "建立 Palace 目錄..."
mkdir -p "$PALACE_PATH"
log_ok "Palace 目錄: $PALACE_PATH"

log_info "執行: mempalace init..."
cd "$PALACE_PATH"
python3 -c "
import sys
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_status
print('Palace initialized')
" 2>&1 | while read line; do
    log_info "$line"
done

log_ok "Palace 初始化完成"

# =============================================================================
# Step 3: 建立 mempalace.yaml 設定檔
# =============================================================================
echo ""
echo "【Step 3/7】建立設定檔"
echo "─────────────────────────────────────────"

MEMPALACE_YAML="$OPENCLAW_PATH/workspace/mempalace.yaml"
log_info "建立: $MEMPALACE_YAML"

mkdir -p "$(dirname "$MEMPALACE_YAML")"

cat > "$MEMPALACE_YAML" << 'YAML'
palace:
  path: ~/.mempalace
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
YAML

log_ok "mempalace.yaml 建立完成"

# =============================================================================
# Step 4: 更新 mcporter.json（MCP Server 設定）
# =============================================================================
echo ""
echo "【Step 4/7】更新 mcporter.json"
echo "─────────────────────────────────────────"

if [ ! -f "$MCPORTER_PATH" ]; then
    log_error "mcporter.json 不存在: $MCPORTER_PATH"
    exit 1
fi

log_info "備份 mcporter.json..."
cp "$MCPORTER_PATH" "$MCPORTER_PATH.bak.$(date +%Y%m%d%H%M%S)"
log_ok "備份完成"

log_info "加入 mempalace MCP Server..."

# 使用 Python 處理 JSON
python3 << PYEOF
import json
import os

mcporter_path = os.path.expanduser("$MCPORTER_PATH")

with open(mcporter_path, 'r') as f:
    config = json.load(f)

# 加入 mempalace server
config['mcpServers']['mempalace'] = {
    "command": "$PYTHON_PATH",
    "args": ["-m", "mempalace.mcp_server", "--palace", "$PALACE_PATH"]
}

with open(mcporter_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("mcporter.json 更新完成")
PYEOF

log_ok "mcporter.json 更新完成"

# =============================================================================
# Step 5: 建立 Hook 目錄與檔案
# =============================================================================
echo ""
echo "【Step 5/7】建立 Hook"
echo "─────────────────────────────────────────"

log_info "建立 Hook 目錄..."
mkdir -p "$HOOK_PATH"
log_ok "Hook 目錄: $HOOK_PATH"

# hook_writer.py
log_info "建立 hook_writer.py..."
cat > "$HOOK_PATH/hook_writer.py" << 'PYEOF'
#!/usr/bin/env python3
"""
MemPalace Session Writer — Phase 2 雙寫整合核心
"""
import sys, json
from datetime import datetime

sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_add_drawer, tool_diary_write

def write_session_summary(session_data: dict) -> dict:
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
PYEOF
chmod +x "$HOOK_PATH/hook_writer.py"
log_ok "hook_writer.py 建立完成"

# wakeup.py
log_info "建立 wakeup.py..."
cat > "$HOOK_PATH/wakeup.py" << 'PYEOF'
#!/usr/bin/env python3
"""
MemPalace Wake-Up Context Generator — Phase 3 核心引擎
"""
import sys, json
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
PYEOF
chmod +x "$HOOK_PATH/wakeup.py"
log_ok "wakeup.py 建立完成"

# mp CLI
log_info "建立 mp CLI..."
cat > "$HOOK_PATH/mp" << 'ZSH'
#!/bin/zsh
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
  *)
    echo "用法: mp [search|diary|taxonomy] [關鍵字...]"
    ;;
esac
ZSH
chmod +x "$HOOK_PATH/mp"
log_ok "mp CLI 建立完成"

# HOOK.json
log_info "建立 HOOK.json..."
cat > "$HOOK_PATH/HOOK.json" << 'JSON'
{
  "name": "mempalace-memory",
  "version": "3.0.0",
  "description": "MemPalace Phase 3 — 完全接管 OpenClaw 記憶系統",
  "author": "King Sean of KS",
  "trigger": {
    "session:compact:after": { "enabled": true, "async": true },
    "gateway:startup": { "enabled": true, "async": true }
  },
  "modules": {
    "main": "handler.ts",
    "hook_writer": "hook_writer.py",
    "wakeup": "wakeup.py",
    "cli": "mp"
  }
}
JSON
log_ok "HOOK.json 建立完成"

# =============================================================================
# Step 6: 安裝 mempalace 技能（SKILL.md）
# =============================================================================
echo ""
echo "【Step 6/7】安裝 mempalace 技能"
echo "─────────────────────────────────────────"

SKILL_MEMPALACE="$SKILLS_PATH/mempalace"
mkdir -p "$SKILL_MEMPALACE"
log_info "技能目錄: $SKILL_MEMPALACE"

cat > "$SKILL_MEMPALACE/SKILL.md" << 'MD'
---
name: mempalace
description: MemPalace 長期記憶系統。King Sean of KS 的 AI 記憶宮殿，提供 RAW verbatim 語意搜尋、知識圖譜、日記功能。觸發關鍵字：搜尋記憶、查歷史、MemPalace、記得我之前說過。
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
MD

log_ok "mempalace 技能安裝完成"

# =============================================================================
# Step 7: 驗證安裝
# =============================================================================
echo ""
echo "【Step 7/7】驗證安裝"
echo "─────────────────────────────────────────"

# 測試 MemPalace
log_info "測試 MemPalace..."
TEST_RESULT=$(python3 - << 'PYEOF'
import sys
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_status
r = tool_status()
print(f"OK:{r.get('total_drawers', 0)}")
PYEOF
)

if [[ "$TEST_RESULT" == OK:* ]]; then
    DRAWERS=$(echo "$TEST_RESULT" | cut -d: -f2)
    log_ok "MemPalace: $DRAWERS drawers"
else
    log_error "MemPalace 測試失敗"
fi

# 測試 mp CLI
log_info "測試 mp CLI..."
if "$HOOK_PATH/mp" status 2>&1 | grep -q "status"; then
    log_ok "mp CLI: 正常"
else
    log_warn "mp CLI: 需要進一步測試"
fi

# =============================================================================
# 完成
# =============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ 安裝完成                                                 ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  請執行以下命令重啟 Gateway:                                  ║"
echo "║                                                              ║"
echo "║    openclaw gateway restart                                  ║"
echo "║                                                              ║"
echo "║  驗證安裝:                                                   ║"
echo "║    python3 ~/.openclaw/hooks/mempalace-memory/wakeup.py      ║"
echo "║    ~/.openclaw/hooks/mempalace-memory/mp diary               ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
