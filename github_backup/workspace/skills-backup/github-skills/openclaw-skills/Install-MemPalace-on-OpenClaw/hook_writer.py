#!/usr/bin/env python3
"""
MemPalace Session Writer — Phase 2 雙寫整合核心
由 OpenClaw Hook 觸發，將 Session 上下文寫入 MemPalace
"""

import sys
import json
import os
from datetime import datetime

# MemPalace Python API
sys.path.insert(0, '/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages')
from mempalace.mcp_server import tool_add_drawer, tool_diary_write


def write_session_summary(session_data: dict) -> dict:
    """將 Session 摘要寫入 MemPalace"""
    wing = session_data.get("wing", "ks-system")
    room = session_data.get("room", "general")
    
    content = session_data.get("content", "")
    source = session_data.get("source", f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    agent = session_data.get("agent", "KingSeanKS")
    
    if not content:
        return {"success": False, "error": "No content to write"}
    
    try:
        result = tool_add_drawer(
            content=content,
            wing=wing,
            room=room,
            source_file=source
        )
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_diary_entry(entry: str, topic: str = "general", agent: str = "KingSeanKS") -> dict:
    """將日記條目寫入 MemPalace"""
    try:
        result = tool_diary_write(
            agent_name=agent,
            entry=entry,
            topic=topic
        )
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_decision(content: str, source: str = None) -> dict:
    """將重要決定寫入 ks-system/decisions"""
    try:
        result = tool_add_drawer(
            content=content,
            wing="ks-system",
            room="decisions",
            source_file=source or f"decision-{datetime.now().strftime('%Y%m%d')}"
        )
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_skill_event(skill_name: str, event: str, content: str) -> dict:
    """將技能相關事件寫入 ks-system/skills"""
    try:
        full_content = f"## {skill_name}: {event}\n\n{content}"
        result = tool_add_drawer(
            content=full_content,
            wing="ks-system",
            room="skills",
            source_file=f"skill-event-{skill_name}-{datetime.now().strftime('%Y%m%d')}"
        )
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # 從 stdin 讀取 JSON 輸入
    try:
        input_data = json.loads(sys.stdin.read())
    except Exception:
        # 沒有輸入，印出使用說明
        print("MemPalace Session Writer")
        print("Usage: cat {json} | python3 hook_writer.py")
        print("")
        print("Input format:")
        print('{"action": "session_summary", "wing": "ks-system", "room": "general", "content": "...", "source": "..."}')
        print('{"action": "diary", "entry": "...", "topic": "general", "agent": "KingSeanKS"}')
        print('{"action": "decision", "content": "...", "source": "..."}')
        print('{"action": "skill_event", "skill_name": "...", "event": "...", "content": "..."}')
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
    elif action == "decision":
        result = write_decision(
            content=input_data.get("content", ""),
            source=input_data.get("source")
        )
    elif action == "skill_event":
        result = write_skill_event(
            skill_name=input_data.get("skill_name", ""),
            event=input_data.get("event", ""),
            content=input_data.get("content", "")
        )
    else:
        result = {"success": False, "error": f"Unknown action: {action}"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
