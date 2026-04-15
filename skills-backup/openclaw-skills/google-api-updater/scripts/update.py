#!/usr/bin/env python3
"""
Google API Key 更新工具
用法：
  python3 ~/.openclaw/skills/google-api-updater/scripts/update.py --project <專案編號> --key <API_KEY>
"""

import json, sys, os, argparse

CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
PROJECT_INFO_PATH = os.path.expanduser("~/.openclaw/skills/google-api-updater/project_info.json")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_api_key(new_key):
    config = load_json(CONFIG_PATH)
    config["skills"]["entries"]["goplaces"]["env"]["GOOGLE_PLACES_API_KEY"] = new_key
    save_json(CONFIG_PATH, config)
    print(f"✅ API Key 已更新：{new_key}")

def save_project_info(project_id, api_key):
    info = {
        "project_id": project_id,
        "api_key": api_key[:12] + "..." + api_key[-6:],  # 只顯示前後片段
        "updated_at": __import__("datetime").datetime.now().isoformat()
    }
    save_json(PROJECT_INFO_PATH, info)
    print(f"✅ 專案編號已記錄：{project_id}")

def main():
    parser = argparse.ArgumentParser(description="更新 Google Places API Key")
    parser.add_argument("--project", required=True, help="Google Cloud 專案編號")
    parser.add_argument("--key", required=True, help="新的 API Key")
    args = parser.parse_args()

    key = args.key.strip()
    project = args.project.strip()

    if not key.startswith("AIza"):
        print("❌ API Key 必須以 AIza 開頭，請確認格式是否正確。")
        sys.exit(1)

    update_api_key(key)
    save_project_info(project, key)
    print("✅ 更新完成！")

if __name__ == "__main__":
    main()
