#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 版本：v1.1.1 (2026-04-29)
# 說明：OpenClaw 啟動預檢自癒腳本 (Immortal Key Healer) - 穩定版
# 變更：移除對 openclaw.json auth.profiles 的強制注入，防止 Schema 衝突導致 Gateway 崩潰。

import os
import subprocess
import json
import re
import sys
import time

# 檔案路徑定義
ENV_PATH = os.path.expanduser("~/.openclaw/.env")
CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
MODELS_PATH = os.path.expanduser("~/.openclaw/agents/main/agent/models.json")
AUTH_PATH = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")

def log(msg):
    print(f"⚕️ [Healer] {msg}", flush=True)

def test_key_liveness(key, retries=2):
    """測試金鑰是否有效，具備重試機制"""
    if not key or not key.startswith("AIza"):
        return False
    
    for i in range(retries):
        cmd = [
            "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
            f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            code = result.stdout.strip()
            if code == "200":
                return True
            if code == "429": # Rate limited
                time.sleep(2 * (i + 1))
                continue
        except Exception:
            pass
        if i < retries - 1: time.sleep(1)
    return False

def extract_keys():
    """從各層級檔案中提取金鑰"""
    keys = {}
    
    # 1. .env
    if os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, 'r') as f:
                content = f.read()
                for var in ['GOOGLE_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_AI_API_KEY']:
                    match = re.search(f'{var}=(AIza[^\s\n]+)', content)
                    if match: 
                        keys['env'] = match.group(1)
                        break
        except: pass
            
    # 2. models.json
    if os.path.exists(MODELS_PATH):
        try:
            with open(MODELS_PATH, 'r') as f:
                data = json.load(f)
                keys['models'] = data.get('providers', {}).get('google-ai', {}).get('apiKey')
        except: pass

    # 3. openclaw.json
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                # 優先查 goplaces
                k = data.get('plugins', {}).get('entries', {}).get('goplaces', {}).get('env', {}).get('GOOGLE_PLACES_API_KEY')
                if k: keys['config'] = k
        except: pass

    return keys

def sync_all(valid_key):
    """執行物理對齊程序"""
    log(f"啟動主權對齊流程，目標金鑰：{valid_key[:10]}...")
    
    targets = [ENV_PATH, CONFIG_PATH, MODELS_PATH, AUTH_PATH]
    
    # 第一步：解除所有目標的實體鎖定
    for path in targets:
        if os.path.exists(path):
            subprocess.run(["chflags", "nouchg", path], capture_output=True)
            os.chmod(path, 0o644)

    # 寫入 .env
    if os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, 'r') as f: lines = f.readlines()
            new_lines = []
            updated = False
            for line in lines:
                if any(var in line for var in ["API_KEY="[SECRET_REDACTED]"GEMINI_API_KEY="[SECRET_REDACTED]'=')[0]
                    new_lines.append(f"{key_type}={valid_key}\n")
                    updated = True
                else:
                    new_lines.append(line)
            if not updated:
                new_lines.append(f"GOOGLE_API_KEY={valid_key}\n")
                new_lines.append(f"GEMINI_API_KEY={valid_key}\n")
            with open(ENV_PATH, 'w') as f: f.writelines(new_lines)
        except: pass

    # 寫入 models.json
    if os.path.exists(MODELS_PATH):
        try:
            with open(MODELS_PATH, 'r') as f: data = json.load(f)
            if 'providers' not in data: data['providers'] = {}
            if 'google-ai' not in data['providers']: data['providers']['google-ai'] = {}
            data['providers']['google-ai']['apiKey'] = valid_key
            with open(MODELS_PATH, 'w') as f: json.dump(data, f, indent=2)
        except: pass

    # 寫入 auth-profiles.json
    if os.path.exists(AUTH_PATH):
        try:
            with open(AUTH_PATH, 'r') as f: data = json.load(f)
            if 'profiles' not in data: data['profiles'] = {}
            for p in ['google:default', 'google-ai:default']:
                if p not in data['profiles']: data['profiles'][p] = {}
                data['profiles'][p]['key'] = valid_key
            with open(AUTH_PATH, 'w') as f: json.dump(data, f, indent=2)
        except: pass

    # 寫入 openclaw.json (僅限 goplaces 插件，避開敏感的 auth 節點)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f: data = json.load(f)
            if 'plugins' in data and 'entries' in data['plugins'] and 'goplaces' in data['plugins']['entries']:
                if 'env' not in data['plugins']['entries']['goplaces']: data['plugins']['entries']['goplaces']['env'] = {}
                data['plugins']['entries']['goplaces']['env']['GOOGLE_PLACES_API_KEY'] = valid_key
                with open(CONFIG_PATH, 'w') as f: json.dump(data, f, indent=2)
        except: pass

    # 第二步：恢復實體鎖定
    for path in targets:
        if os.path.exists(path):
            subprocess.run(["chflags", "uchg", path], capture_output=True)
    
    log("✅ 所有配置已完成物理對齊與鎖定。")

def main():
    log("開始執行啟動預檢...")
    keys = extract_keys()
    
    unique_candidates = []
    seen = set()
    for k in keys.values():
        if k and k not in seen:
            unique_candidates.append(k)
            seen.add(k)

    if not unique_candidates:
        log("⚠️ 未偵測到任何金鑰，跳過自癒。")
        return

    valid_key = None
    for k in unique_candidates:
        if test_key_liveness(k):
            valid_key = k
            break

    if not valid_key:
        log("❌ 偵測到的金鑰全數失效，請手動更新 .env！")
        return

    mismatched_sources = [src for src, val in keys.items() if val != valid_key]
    if mismatched_sources:
        log(f"發現不一致層級：{', '.join(mismatched_sources)}。")
        sync_all(valid_key)
    else:
        log("✨ 所有層級金鑰均一致且有效，系統健康。")

if __name__ == "__main__":
    main()
