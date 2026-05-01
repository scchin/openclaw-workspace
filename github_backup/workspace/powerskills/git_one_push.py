import subprocess
import sys
import argparse

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return None
    return result.stdout.strip()

def git_one_push(message=None):
    print("🚀 [PowerSkill] Initiating Git One-Push Sync...")
    
    # 1. Check status
    status = run("git status --short")
    if not status:
        print("✅ No changes to sync.")
        return
    
    print(f"📦 Detected changes:\n{status}")
    
    # 2. Add
    run("git add .")
    
    # 3. Commit
    if not message:
        # Auto-generate a simple message if none provided
        message = f"GURF Auto-Sync: {len(status.splitlines())} files modified"
    
    commit_res = run(f'git commit -m "{message}"')
    if commit_res:
        print(f"📝 Commit success: {message}")
    
    # 4. Push
    print("☁️ Pushing to remote...")
    push_res = run("git push")
    if push_res is not None:
        print("🎉 Sync complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Git One-Push: Consolidate Git workflow into a single turn.")
    parser.add_argument("-m", "--message", help="Commit message")
    args = parser.parse_args()
    
    git_one_push(args.message)
