import sys
import os

# 引入現有的 sanitizer 邏輯
sys.path.append("/Users/KS/.openclaw/workspace")
from output_sanitizer import sanitize_text

def atomic_write_sanitized(target_file, raw_content):
    print(f"🧹 [Atomic] Sanitizing and writing to {target_file}...")
    
    # 執行清洗
    clean_content = sanitize_text(raw_content)
    
    # 寫入檔案
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(clean_content)
        print(f"✅ Success. {len(clean_content)} bytes written.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 atomic_write_sanitized.py <file> <content>")
        sys.exit(1)
    
    target = sys.argv[1]
    content = sys.argv[2]
    atomic_write_sanitized(target, content)
