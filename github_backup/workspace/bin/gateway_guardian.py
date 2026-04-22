import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
import glob
import re

# =============================================================================
# [穩健版] VERSION: v2026.04.21-RegexPurify
# 說明：升級過濾引擎，優化對 LaTeX \text{} 內容的動態提取，確保數學/物理格式顯示。
# 變更：
# 1. 修改 get_purify_engine_js，新增正則表達式還原邏輯。
# 2. 強化 node --check 的路徑獲取邏輯，提高預檢準確度。
# =============================================================================

GATEWAY_DIST_DIR = "/opt/homebrew/lib/node_modules/openclaw/dist"
SIGNATURE = "_purify"
RULES_PATH = "/Users/KS/.openclaw/workspace/Sutra_Library/S-Swarm_Hybrid_System/intercept_rules.json"

def load_rules_as_js_obj():
    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            rules = json.load(f).get("latex_to_unicode", {})
        js_pairs = [f"'{k}' : '{v}'" for k, v in rules.items()]
        return "{" + ", ".join(js_pairs) + "}"
    except Exception as e:
        return "{}"

def get_purify_engine_js():
    rules_obj = load_rules_as_js_obj()
    return f'''
// --- PURIFY ENGINE START ---
const _purify = (obj) => {{
    const replacements = {rules_obj};
    if (typeof obj === 'string') {{
        let content = obj;
        // 1. [穩健模式] 先處理動態標籤內容提取 (如 \\\\text{{GB}} -> GB)
        content = content.replace(/\\\\text\{{([^}}]*)\}}/g, '$1');
        
        // 2. 處理固定符號對應
        const sortedPatterns = Object.keys(replacements).sort((a, b) => b.length - a.length);
        for (const pattern of sortedPatterns) {{
            content = content.split(pattern).join(replacements[pattern]);
        }}
        
        // 3. 處理剩餘的 LaTeX 定界符 (處理可能重複轉義的情況)
        return content.replace(/\\\\\\\\\\$/g, '').replace(/\\\\\\$/g, '').replace(/\\$/g, '');
    }} else if (Array.isArray(obj)) {{
        return obj.map(_purify);
    }} else if (obj !== null && typeof obj === 'object') {{
        const newObj = {{}};
        for (const key in obj) {{
            newObj[key] = _purify(obj[key]);
        }}
        return newObj;
    }}
    return obj;
}};
// --- PURIFY ENGINE END ---
'''

def inject_purify(file_path):
    print(f"🔍 Analyzing bundle: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 清理舊版標記，防止重複注入
    if "// --- PURIFY ENGINE START ---" in content:
        content = re.sub(r'// --- PURIFY ENGINE START ---.*?// --- PURIFY ENGINE END ---\n?', '', content, flags=re.DOTALL)
        print("♻️ Removing old engine markers...")
    
    engine_js = get_purify_engine_js()
    # 找到第一個語法出口點進行注入
    injection_point = content.find(';') + 1
    new_content = content[:injection_point] + "\n" + engine_js + content[injection_point:]
    
    # 強制截獲 JSON.stringify 的輸出
    updated_content = re.sub(r'JSON\.stringify\((obj)\)', 'JSON.stringify(_purify(obj))', new_content)
    if updated_content == new_content:
        updated_content = re.sub(r'JSON\.stringify\(([^,)]+)\)', 'JSON.stringify(_purify(\\1))', new_content)

    temp_path = file_path + ".tmp.js"
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    try:
        # 強制執行二進制預檢 (尋找 node 路徑)
        node_bin = "/opt/homebrew/bin/node" if os.path.exists("/opt/homebrew/bin/node") else "node"
        subprocess.run([node_bin, "--check", temp_path], check=True, capture_output=True)
    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        print(f"❌ SYNTAX ERROR DETECTED DURING PRE-FLIGHT: {e}")
        return False
        
    os.replace(temp_path, file_path)
    print("✨ Robust validation complete. Engine injected.")
    return True

def main():
    try:
        pattern = os.path.join(GATEWAY_DIST_DIR, "server.impl-*.js")
        files = glob.glob(pattern)
        if not files: return
        inject_purify(files[0])
    except Exception as e:
        print(f"❌ Guardian Error: {e}")

if __name__ == "__main__":
    main()
