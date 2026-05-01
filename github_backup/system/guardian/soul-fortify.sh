#!/bin/bash
# [SENSITIVE_TOKEN_HARD_REDACTED]--------------
# OpenClaw Soul Fortify (不朽三位一體之裝甲工程師)
# 版本: v4.0 (Omni-Trinity v4.0 - Sentinel Edition)
# 作用: IP 偵測、權限管理、LaTeX 淨化、隱私脫敏、結構修復、全域哨兵掃描。
# [SENSITIVE_TOKEN_HARD_REDACTED]--------------

# 定義路徑
BASE_DIR="$HOME/.openclaw"
GUARDIAN_DIR="$BASE_DIR/guardian"
OPENCLAW_JSON="$BASE_DIR/openclaw.json"
PLIST_PATH="$HOME/Library/LaunchAgents/ai.openclaw.gateway.plist"
ENV_FILE="$BASE_DIR/.env"
RULES_PATH="$BASE_DIR/workspace/Sutra_Library/S-Swarm_Hybrid_System/intercept_rules.json"
GATEWAY_DIST_DIR="/opt/homebrew/lib/node_modules/openclaw/dist"
SKILLS_DIR="$BASE_DIR/workspace/skills"

# =============================================================================
# 1. 偵測 IP (優先抓取 ZeroTier)
# =============================================================================
get_lan_ip() {
    zt_ip=$(ifconfig | grep -E "feth|zt" -A 2 | grep "inet " | awk '{print $2}' | head -n 1)
    [ -z "$zt_ip" ] && zt_ip=$(ifconfig | grep "inet " | grep "192.168.19" | awk '{print $2}' | head -n 1)
    [ -n "$zt_ip" ] && echo "$zt_ip" || ifconfig | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | head -n 1
}

# =============================================================================
# 2. Omni-Sentinel (不朽哨兵：全量技能掃描與排毒)
# =============================================================================
omni_sentinel() {
    echo "🛡️ [Omni-Sentinel] 正在巡檢 Skills 目錄執行「基因排毒」..."
    
    # 掃描並修剪冗餘規則 (LaTeX, PII Masking, Global Identity)
    # 使用 Python 進行精確掃描以避免 Shell 轉義問題
    python3 -c "
import os, re

SKILLS_DIR = '$SKILLS_DIR'
REDUNDANT_PATTERNS = [
    r'\\\\text\{', 
    r'PII filtering', 
    r'隱私過濾', 
    r'秘密金鑰', 
    r'API Key.*filtering',
    r'Markdown.*修正'
]

def prune_skill(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for pattern in REDUNDANT_PATTERNS:
        # 將冗餘行標註為 [REDUNDANT] 而非直接刪除，以便追蹤，並在下個版本物理移除
        content = re.sub(f'(?i)^.*{pattern}.*$', r'# [OMNI-SENTINEL: REDUNDANT RULE REMOVED]', content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✅ 已清理冗餘規則: {os.path.basename(file_path)}')

for root, dirs, files in os.walk(SKILLS_DIR):
    for file in files:
        if file == 'SKILL.md':
            prune_skill(os.path.join(root, file))
"
}

# =============================================================================
# 3. 核心淨化與多層過濾注入 (v4.0 Kernel Matrix)
# =============================================================================
purify_kernel() {
    echo "🔍 [Omni-Check] 執行 v4.0 物理防線巡檢..."
    BUNDLE_FILES=($GATEWAY_DIST_DIR/server.impl-*.js)
    if [ ! -e "${BUNDLE_FILES[0]}" ]; then echo "⚠️ 內核未找到。"; return; fi
    TARGET_BUNDLE="${BUNDLE_FILES[0]}"

    python3 -c "
import os, json, subprocess, re

RULES_PATH = '$RULES_PATH'
TARGET_FILE = '$TARGET_BUNDLE'

def load_rules():
    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            rules = json.load(f).get('latex_to_unicode', {})
        return '{' + ', '.join([f'\"{k}\": \"{v}\"' for k, v in rules.items()]) + '}'
    except: return '{}'

def run_inject():
    with open(TARGET_FILE, 'r', encoding='utf-8') as f: content = f.read()
    if '// --- OMNI-TRINITY v4.0 START ---' in content:
        print('🛡️ 內核已受 v4.0 物理防線保護。')
        return

    # 清理舊版注入
    content = re.sub(r'// --- (PURIFY ENGINE|OMNI-TRINITY v3.0) START ---.*?// --- (PURIFY ENGINE|OMNI-TRINITY v3.0) END ---', '', content, flags=re.DOTALL)

    print('🚀 注入 v4.0 物理矩陣 (隱私脫敏 + 結構自癒 + 符號修復)...')
    rules_obj = load_rules()
    
    engine_js = f'''
// --- OMNI-TRINITY v4.0 START ---
const _omniPurify = (obj) => {{
    const replacements = {{rules_obj}};
    if (typeof obj === 'string') {{
        let c = obj;
        // 隱私脫敏
        c = c.replace(/AIza[0-9A-Za-z-_]{{35}}/g, '[PROTECTED_API_KEY]');
        // 結構修復
        const openCodeBlocks = (c.match(/```/g) || []).length;
        if (openCodeBlocks % 2 !== 0) c += '\\n```'; 
        c = c.replace(/[\\u200B-\\u200D\\uFEFF]/g, '');
        // LaTeX 淨化
        c = c.replace(/\\\\\\\\text\\{{([^}}]*)\\}}/g, '\\$1');
        const sorted = Object.keys(replacements).sort((a, b) => b.length - a.length);
        for (const p of sorted) c = c.split(p).join(replacements[p]);
        return c.replace(/\\\\\\\\\\\\\\$/g, '').replace(/\\\\\\\\\\$/g, '').replace(/\\\\\\$/g, '');
    }}
    if (Array.isArray(obj)) return obj.map(_omniPurify);
    if (obj !== null && typeof obj === 'object') {{
        const n = {{}}; for (const k in obj) n[k] = _omniPurify(obj[k]); return n;
    }}
    return obj;
}};
// --- OMNI-TRINITY v4.0 END ---
'''
    point = content.find(';') + 1
    new_c = content[:point] + '\\n' + engine_js + content[point:]
    new_c = re.sub(r'JSON\\.stringify\\((obj)\\)', 'JSON.stringify(_omniPurify(obj))', new_c)
    if new_c == content:
        new_c = re.sub(r'JSON\\.stringify\\(([^,)]+)\\)', 'JSON.stringify(_omniPurify(\\\\1))', new_c)

    tmp = TARGET_FILE + '.tmp.js'
    with open(tmp, 'w', encoding='utf-8') as f: f.write(new_c)
    try:
        node_bin = '/opt/homebrew/bin/node' if os.path.exists('/opt/homebrew/bin/node') else 'node'
        subprocess.run([node_bin, '--check', tmp], check=True, capture_output=True)
        os.replace(tmp, TARGET_FILE)
        print('✨ v4.0 內核注入成功。')
    except Exception as e:
        if os.path.exists(tmp): os.remove(tmp)
        print(f'❌ v4.0 預檢失敗: {e}')

run_inject()
"
}

# =============================================================================
# 4. 更新配置與啟動
# =============================================================================
update_config() {
    local NEW_IP=$1
    [ -z "$NEW_IP" ] && return
    echo "📡 [Omni-Check] 偵測到 LAN IP: $NEW_IP"
    chflags nouchg "$OPENCLAW_JSON"
    python3 -c "
import json
path = '$OPENCLAW_JSON'
with open(path, 'r') as f: data = json.load(f)
origins = data.get('gateway', {}).get('controlUi', {}).get('allowedOrigins', [])
new_o = f'http://{NEW_IP}:18791'
if new_o not in origins:
    origins.append(new_o); print(f'✅ 已將 {new_o} 加入白名單')
with open(path, 'w') as f: json.dump(data, f, indent=2)
"
    chflags uchg "$OPENCLAW_JSON"
}

# =============================================================================
# 5. GURF Sovereign Alignment (不朽主權對齊)
# =============================================================================
gurf_alignment() {
    echo "🧬 [GURF] 正在執行主權治理對齊與行為攔截巡檢..."
    # 執行基因哨兵進行全量對齊 (自動從 DNA 恢復受損檔案)
    python3 /Users/KS/.openclaw/workspace/system_gene_sentry.py --intensity STANDARD
    
    # 執行物理堡壘進行行為獵殺
    python3 /Users/KS/.openclaw/lib/workspace_guardian.py
}

# 執行主選單
IP=$(get_lan_ip)
update_config "$IP"
omni_sentinel
purify_kernel
gurf_alignment
