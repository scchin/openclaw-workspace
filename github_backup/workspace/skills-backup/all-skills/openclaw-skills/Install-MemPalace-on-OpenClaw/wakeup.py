#!/usr/bin/env python3
"""
MemPalace Wake-Up Context Generator — Phase 3 核心引擎
每次 Session 啟動時，用最少的 Token 注入最大的上下文

目標：舊制 ~2500 tokens → 新制 ~300 tokens（88% 節省）
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import (
    tool_search,
    tool_diary_read,
    tool_get_taxonomy,
    tool_status
)


def get_status_line() -> str:
    """取得 Palace 狀態（1行）"""
    try:
        r = tool_status()
        drawers = r.get('total_drawers', '?')
        return f"- 🏛️ Palace: {drawers} drawers active"
    except:
        return "- 🏛️ Palace: active"


def get_diary_lines(limit: int = 2) -> list:
    """取得最近日記（幾行）"""
    try:
        r = tool_diary_read(agent_name="KingSeanKS", last_n=limit)
        entries = r.get('entries', [])
        if not entries:
            return []
        
        lines = ["- 📅 最近:"]
        for e in entries[-limit:]:
            content = e.get('content', '')[:70]
            lines.append(f"  • {e.get('date')} {content}...")
        return lines
    except:
        return []


def get_principles_line() -> str:
    """取得核心原則摘要（1行）"""
    try:
        r = tool_search(query="核心原則 霸王條款 分工界線 刪除決定", limit=1)
        results = r.get('results', [])
        if results:
            text = results[0].get('text', '')[:100].replace('\n', ' ')
            return f"- ⚠️ 原則: {text}..."
    except:
        pass
    return ""


def get_skills_lines(limit: int = 3) -> list:
    """取得相關技能（幾行）"""
    try:
        r = tool_search(query="自建技能 King Sean of KS", limit=limit)
        results = r.get('results', [])
        if not results:
            return []
        
        lines = ["- 🛠️ 相關技能:"]
        seen = set()
        for res in results:
            text = res.get('text', '')
            for line in text.split('\n'):
                if line.strip().startswith('name:'):
                    skill = line.replace('name:', '').strip()
                    if skill and skill not in seen and len(skill) < 30:
                        seen.add(skill)
                        lines.append(f"  • {skill}")
            if len(seen) >= limit:
                break
        return lines if len(lines) > 1 else []
    except:
        return []


def get_compact_context(topic: str = "King Sean of KS", limit: int = 5) -> str:
    """
    取得緊湊的喚醒上下文（目標 < 400 tokens）
    """
    lines = []
    lines.append("## 📜 MemPalace Wake-Up Context")

    lines.append(get_status_line())
    lines.extend(get_diary_lines(limit=2))
    p = get_principles_line()
    if p:
        lines.append(p)
    lines.extend(get_skills_lines(limit=3))

    lines.append("---")
    lines.append("*更多請用 `mp search \"關鍵字\"` 查詢 MemPalace*")

    return "\n".join(lines)


def get_full_context(topic: str = "King Sean of KS 系統 技能 記憶 決定", limit: int = 8) -> str:
    """
    取得完整上下文（用於需要更多背景時）
    """
    lines = []
    lines.append("=" * 54)
    lines.append("  MemPalace Full Context")
    lines.append("=" * 54)

    # Status
    try:
        r = tool_status()
        drawers = r.get('total_drawers', '?')
        wings = list(r.get('wings', {}).keys())
        lines.append(f"\n📊 Palace 狀態: {drawers} drawers")
        lines.append(f"   Wings: {', '.join(wings)}")
    except Exception as e:
        lines.append(f"\n📊 Palace 狀態: error ({e})")

    # Diary
    try:
        r = tool_diary_read(agent_name="KingSeanKS", last_n=5)
        entries = r.get('entries', [])
        lines.append(f"\n📅 最近日記 ({len(entries)} 筆):")
        for e in entries:
            content = e.get('content', '')[:70]
            lines.append(f"  • {e.get('date')} [{e.get('topic')}]: {content}...")
    except Exception as e:
        lines.append(f"\n📅 日記: error ({e})")

    # Search
    try:
        r = tool_search(query=topic, limit=limit)
        results = r.get('results', [])
        lines.append(f"\n🔍 搜尋「{topic}」（{len(results)} 結果):")
        for res in results[:5]:
            wing = res.get('wing', '')
            room = res.get('room', '')
            sim = res.get('similarity', 0)
            text = res.get('text', '')[:80].replace('\n', ' ')
            lines.append(f"  • [{wing}/{room}] sim={sim:.2f}")
            lines.append(f"    {text}...")
    except Exception as e:
        lines.append(f"\n🔍 搜尋: error ({e})")

    lines.append("=" * 54)
    lines.append("\n💡 用 `mp search \"關鍵字\"` 查詢更多")

    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    """粗估 token 數量"""
    return len(text) // 4


def main():
    mode = "compact"
    topic = "King Sean of KS 系統 技能 記憶"
    limit = 5

    args = sys.argv[1:]
    if "-f" in args or "--full" in args:
        mode = "full"
        args = [a for a in args if a not in ["-f", "--full"]]
    if "-h" in args or "--help" in args:
        print("用法: wakeup.py [-f|--full] [搜尋主題]")
        print("  -f, --full: 輸出完整上下文（預設為緊湊版）")
        sys.exit(0)

    if args:
        topic = " ".join(args)

    if mode == "compact":
        result = get_compact_context(topic=topic, limit=limit)
    else:
        result = get_full_context(topic=topic, limit=limit)

    tokens = estimate_tokens(result)
    print(result)
    print(f"\n[Token 估算: ~{tokens}]", file=sys.stderr)


if __name__ == "__main__":
    main()
