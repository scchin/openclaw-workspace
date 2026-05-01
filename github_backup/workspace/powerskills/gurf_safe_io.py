import os
import argparse
import subprocess

def get_safe_size(path, depth=1):
    """
    不朽架構授權之 I/O 指令。
    強制執行 depth 限制，並避開黑洞目錄。
    """
    print(f"🛡️ [Safe-IO] Executing policy-compliant scan for: {path} (Depth: {depth})")
    
    # 檢查是否為黑洞目錄
    blackholes = ["backups", "repo", "node_modules", ".venv"]
    if any(bh in path.lower() for bh in blackholes) and depth > 1:
        print(f"⚠️ [WARNING] Detected I/O Blackhole. Depth restricted to 1 for safety.")
        depth = 1

    cmd = f"du -hd {depth} \"{path}\""
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            print(res.stdout)
            return True
        else:
            print(f"❌ Error: {res.stderr}")
            return False
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GURF Authorized Safe-IO Tool")
    parser.add_argument("--path", required=True, help="Path to analyze")
    parser.add_argument("--depth", type=int, default=1, help="Max depth (Default 1)")
    args = parser.parse_args()
    
    get_safe_size(args.path, args.depth)
