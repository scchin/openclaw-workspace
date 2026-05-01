import os
import re
import glob

class PathResolver:
    """
    Handles the identification and calibration of absolute paths across 
    the OpenClaw system to ensure seamless migration between machines.
    """
    
    def __init__(self, old_root=None, new_root=None):
        self.old_root = old_root
        self.new_root = new_root

    def detect_user_home(self, path):
        """Detects the user home directory pattern in a given path."""
        # Pattern matches /Users/username/
        match = re.match(r'(/Users/[^/]+)', path)
        return match.group(1) if match else None

    def calibrate_file(self, file_path):
        """
        Reads a file, replaces all occurrences of the old user home 
        with the new user home, and writes it back.
        """
        if not self.old_root or not self.new_root:
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if self.old_root in content:
                new_content = content.replace(self.old_root, self.new_root)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
        except Exception as e:
            print(f"Error calibrating {file_path}: {e}")
        return False

    def calibrate_recursive(self, root_dir):
        """
        Recursively scans a directory for text-based files and calibrates paths.
        """
        # [FIX] 加入 .plist 支援，確保 LaunchAgent 路徑在新電腦上也能正確校正
        extensions = ('.json', '.md', '.py', '.js', '.yaml', '.yml', '.env', '.txt', '.plist')
        count = 0
        
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith(extensions):
                    full_path = os.path.join(root, file)
                    if self.calibrate_file(full_path):
                        count += 1
        return count
