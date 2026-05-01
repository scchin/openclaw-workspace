import sys
import re

def check_command(cmd):
    # Forbidden patterns: du or find without depth limits on large directories
    # Specifically looking for recursive du or find without -maxdepth or -d
    
    # 1. Check for 'du' without depth limit
    if 'du' in cmd:
        if not (re.search(r'-d \d+', cmd) or re.search(r'--max-depth=\d+', cmd)):
            return False, "CRITICAL: 'du' detected without depth limit (-d or --max-depth). This will cause I/O blocking on large directories."
    
    # 2. Check for 'find' without depth limit
    if 'find' in cmd:
        if not (re.search(r'-maxdepth \d+', cmd)):
            return False, "CRITICAL: 'find' detected without -maxdepth. This will cause I/O blocking."
            
    # 3. Check for custom python scripts that might be recursive
    if 'python' in cmd and 'get_dir_size' in cmd:
        return False, "CRITICAL: Custom recursive size function detected. Use 'du -d 1' instead."

    return True, "PASS: Command follows IO_PROTOCOL."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 io_guard.py \"command\"")
        sys.exit(1)
    
    command = sys.argv[1]
    passed, message = check_command(command)
    
    if passed:
        print(f"✅ [IO_GUARD] {message}")
        sys.exit(0)
    else:
        print(f"❌ [IO_GUARD] {message}")
        sys.exit(1)
