import sys
import os
import re

# 配置文件路徑
REGISTRY_PATH = "/Users/KS/.openclaw/workspace/EXPERT_REGISTRY.md"

def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        print(f"Error: Registry file not found at {REGISTRY_PATH}")
        return []
    
    experts = []
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # 尋找表格起始行
        start_index = -1
        for i, line in enumerate(lines):
            if "| 專家名稱 | 核心專長 |" in line:
                start_index = i + 2 # 跳過標題行和分隔行
                break
        
        if start_index == -1:
            return []
            
        for line in lines[start_index:]:
            if line.strip() and "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 4:
                    experts.append({
                        "name": parts[0],
                        "expertise": parts[1],
                        "archetype": parts[2],
                        "logic": parts[3]
                    })
    return experts

def dispatch(query):
    experts = load_registry()
    if not experts:
        return "No experts registered. Falling back to General AI."

    # 計算所有專家的匹配得分
    scored_experts = []
    for expert in experts:
        score = 0
        expertise_keywords = expert['expertise'].split('/')
        for kw in expertise_keywords:
            if kw.strip() in query:
                score += 10
        
        if expert['archetype'] in query:
            score += 5
            
        scored_experts.append((score, expert))
    
    # 按得分由高到低排序
    scored_experts.sort(key=lambda x: x[0], reverse=True)
    
    # 提取得分大於 0 的前 3 位專家
    panel = [exp for score, exp in scored_experts if score > 0][:3]
    
    if not panel:
        # 若無任何匹配，預設派遣頂層戰略專家
        panel = [experts[0]]
            
    return panel

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 dispatch.py \"<query>\"")
        sys.exit(1)
        
    user_query = sys.argv[1]
    result = dispatch(user_query)
    
    if isinstance(result, list):
        print(f"DISPATCH_MODE: PANEL")
        print(f"TOTAL_EXPERTS: {len(result)}")
        for i, expert in enumerate(result):
            print(f"EXPERT_{i+1}_NAME: {expert['name']}")
            print(f"EXPERT_{i+1}_EXPERTISE: {expert['expertise']}")
            print(f"EXPERT_{i+1}_ARCHETYPE: {expert['archetype']}")
            print(f"EXPERT_{i+1}_LOGIC: {expert['logic']}")
    else:
        print(result)
