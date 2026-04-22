import os
import sys
import subprocess
import argparse

# OpenClaw Fortress Orchestrator v1.0
# The official entry point for the Immortal Trinity Architecture.

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIC_DIR = os.path.join(SKILL_DIR, "logic")
EXTENSIONS_DIR = os.path.join(SKILL_DIR, "extensions")

class Fortress:
    def __init__(self):
        self.fortify_script = os.path.join(LOGIC_DIR, "fortify.sh")
        self.guardian_script = os.path.join(LOGIC_DIR, "guardian_logic.py")

    def fortify(self, mode="--check"):
        """執行系統強化與 IP 自適應校對"""
        print(f"🛡️ [Fortress] Starting fortification (mode: {mode})...")
        try:
            # 執行核心 Shell 邏輯
            subprocess.run(["bash", self.fortify_script, mode], check=True)
            
            # 執行擴充插件邏輯
            self._apply_extensions()
            
            print("✅ [Fortress] Fortification completed.")
        except Exception as e:
            print(f"❌ [Fortress] Fortification failed: {e}")

    def _apply_extensions(self):
        """掃描並執行 extensions/ 資料夾下的自定義腳本"""
        if not os.path.exists(EXTENSIONS_DIR):
            return
            
        print("🔍 [Fortress] Scanning for extensions...")
        for file in sorted(os.listdir(EXTENSIONS_DIR)):
            if file.endswith(".sh"):
                ext_path = os.path.join(EXTENSIONS_DIR, file)
                print(f"🧩 [Extension] Executing {file}...")
                subprocess.run(["bash", ext_path], check=False)

    def monitor(self):
        """啟動金鑰真相守護進程"""
        print("📡 [Fortress] Launching Key Guardian daemon...")
        try:
            # 背景執行 guardian
            subprocess.Popen(["python3", self.guardian_script], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            print("✅ [Fortress] Guardian is now monitoring keys in background.")
        except Exception as e:
            print(f"❌ [Fortress] Failed to launch guardian: {e}")

    def install(self):
        """執行全自動系統注入 (Bootstrap)"""
        print("🏗️ [Fortress] Installing Immortal Trinity Architecture...")
        self.fortify(mode="--install")

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Fortress CLI")
    parser.add_argument("command", choices=["install", "fortify", "monitor", "verify"], help="Command to execute")
    
    args = parser.parse_args()
    fortress = Fortress()

    if args.command == "install":
        fortress.install()
    elif args.command == "fortify":
        fortress.fortify()
    elif args.command == "monitor":
        fortress.monitor()
    elif args.command == "verify":
        fortress.fortify(mode="--check")

if __name__ == "__main__":
    main()
