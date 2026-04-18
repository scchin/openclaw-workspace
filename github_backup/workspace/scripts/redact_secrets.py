#!/usr/bin/env python3
import os
import re
import sys

# =============================================================================
# 🛡️ OpenClaw Secret Redactor (Physical Guard)
# =============================================================================

# 敏感模式定義
SECRET_PATTERNS = [
    # GCP API Keys (Stronger pattern)
    (re.compile(r'AIza[A-Za-z0-9_-]{30,100}'), '[GCP_API_KEY_REDACTED]'),
    # OpenAI API Keys
    (re.compile(r'sk-[a-zA-Z0-9]{30,100}'), '[OPENAI_KEY_REDACTED]'),
    # Generic high-entropy keys (Stricter: only if length is 32-64, avoid long random strings in code)
    (re.compile(r'(?<![a-zA-Z0-9])([a-zA-Z0-9]{32,64})(?![a-zA-Z0-9])'), '[GENERIC_SECRET_REDACTED]'),
    # Context-based secrets: key = "value" or key: "value"
    (re.compile(r'((?:api_key|secret|token|password|private_key|apiKey|secretKey)\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1[SECRET_REDACTED]\3'),
]

def redact_text(text):
    """對文本進行多輪脫敏處理"""
    original_text = text
    # 1. 標準模式匹配
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    
    # 2. 強制模式：針對所有 32-64 位的高熵字串進行抹除 (不論前綴)
    # This is the "Nuclear Option" for stubborn keys
    text = re.sub(r'(?<![a-zA-Z0-9])([a-zA-Z0-9_-]{32,64})(?![a-zA-Z0-9])', '[SENSITIVE_TOKEN_HARD_REDACTED]', text)
    
    return text

def process_directory(target_dir, dry_run=False):
    """遞迴處理目錄下所有文件"""
    found_secrets = 0
    for root, _, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                redacted_content = redact_text(content)
                
                if redacted_content != content:
                    found_secrets += 1
                    if not dry_run:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(redacted_content)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                
    return found_secrets

def audit_directory(target_dir):
    """檢查目錄中是否仍殘留敏感資訊 (Pre-push Audit)"""
    leak_found = False
    for root, _, files in os.walk(target_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for pattern, _ in SECRET_PATTERNS:
                        if pattern.search(content):
                            print(f"🚨 LEAK DETECTED in {file_path}")
                            leak_found = True
                            break
            except Exception:
                pass
    return leak_found

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: redact_secrets.py [redact|audit] [directory]")
        sys.exit(1)
        
    mode = sys.argv[1]
    target = sys.argv[2]
    
    if mode == "redact":
        count = process_directory(target)
        print(f"✅ Redaction complete. Files modified: {count}")
    elif mode == "audit":
        if audit_directory(target):
            print("❌ Audit failed: Secrets still present!")
            sys.exit(1)
        else:
            print("✅ Audit passed: No secrets found.")
            sys.exit(0)
    else:
        print("Invalid mode. Use 'redact' or 'audit'.")
        sys.exit(1)
