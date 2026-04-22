import os
import requests
import tarfile
import shutil
from pathlib import Path

# Configuration
REPO = "scchin/openclaw-soul-backups"
TARGET_HOME = Path(os.path.expanduser("~"))
TMP_DIR = TARGET_HOME / ".openclaw/restore_raw_tmp"

def main():
    # Try the latest backup prefix
    prefix = "soul_core_20260419_1934"
    archive_final = TARGET_HOME / f"{prefix}.tar.gz"
    
    print(f"🚀 Attempting RAW binary pull for {prefix}...")
    
    try:
        with open(archive_final, 'wb') as combined:
            for i in range(1, 100): # Try up to 100 parts
                part_name = f"{prefix}.tar.gz.part{i}"
                url = f"https://raw.githubusercontent.com/{REPO}/main/{part_name}"
                
                res = requests.get(url)
                if res.status_code == 404:
                    print(f"🏁 Reached end of chunks at part {i-1}.")
                    break
                if res.status_code != 200:
                    print(f"⚠️ Part {i} failed to download (Status: {res.status_code})")
                    break
                
                combined.write(res.content)
                print(f"📥 Downloaded raw {part_name}")

        # Test the result
        with open(archive_final, 'rb') as f:
            header = f.read(2)
            if header == b'\\x1f\\x8b':
                print("🎉 SUCCESS! Raw pull recovered the Gzip header.")
                # Perform restoration...
                if not TMP_DIR.exists(): TMP_DIR.mkdir(parents=True)
                with tarfile.open(archive_final, "r:gz") as tar:
                    tar.extractall(path=TMP_DIR)
                print("✅ System restored from RAW pull.")
            else:
                print(f"❌ Failed. Raw header is {header.hex()}. Still not a Gzip file.")
                
    except Exception as e:
        print(f"❌ Critical error: {e}")
    finally:
        if archive_final.exists(): os.remove(archive_final)
        if TMP_DIR.exists(): shutil.rmtree(TMP_DIR)

if __name__ == "__main__":
    main()
