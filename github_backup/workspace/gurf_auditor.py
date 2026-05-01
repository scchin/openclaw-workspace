import re
import json
from collections import Counter
from datetime import datetime

LOG_PATH = "/Users/KS/.openclaw/logs/gateway.log"
OUTPUT_PATH = "/Users/KS/.gemini/antigravity/brain/[SENSITIVE_TOKEN_HARD_REDACTED]/merge_recommendations.json"

# 正則表達式：捕獲工具名稱與時間戳
# 範例：2026-04-23T11:32:02.039+08:00 [ws] ⇄ res ✓ commands.list 6841ms ...
LOG_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}\+08:00) .*? ✓ ([\w\.]+)")

def audit_logs():
    print(f"🧐 [Auditor] Scanning {LOG_PATH} for fragmented patterns...")
    
    sequences = []
    current_sequence = []
    last_timestamp = None
    
    try:
        with open(LOG_PATH, "r") as f:
            for line in f:
                match = LOG_PATTERN.search(line)
                if match:
                    ts_str, tool = match.groups()
                    ts = datetime.fromisoformat(ts_str.replace("+08:00", ""))
                    
                    # 如果兩個工具呼叫間隔小於 10 秒，視為同一個邏輯鏈
                    if last_timestamp and (ts - last_timestamp).total_seconds() > 10:
                        if len(current_sequence) > 1:
                            sequences.append(tuple(current_sequence))
                        current_sequence = []
                    
                    # 排除常見的背景心跳工具 (如 node.list)
                    if tool not in ["node.list", "sessions.list", "models.list", "device.pair.list"]:
                        current_sequence.append(tool)
                        last_timestamp = ts
            
            if len(current_sequence) > 1:
                sequences.append(tuple(current_sequence))
    except FileNotFoundError:
        print("❌ [Auditor] Log file not found.")
        return

    # 統計重複出現的工具鏈
    sequence_counts = Counter(sequences)
    
    recommendations = []
    for seq, count in sequence_counts.most_common(10):
        recommendations.append({
            "sequence": list(seq),
            "occurrence": count,
            "suggestion": f"偵測到重複調用鏈：{' -> '.join(seq)}。建議整合為單一複合工具。"
        })

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_sequences_analyzed": len(sequences),
        "top_merge_candidates": recommendations
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ [Auditor] Audit complete. Recommendations saved to {OUTPUT_PATH}")
    return report

if __name__ == "__main__":
    audit_logs()
