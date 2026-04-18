import json
import os
import ssl
import shutil
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Configuration Paths
BASE_DIR = Path.home() / ".openclaw"
CONFIG_FILE = BASE_DIR / "openclaw.json"
AUTH_FILE = BASE_DIR / "agents/main/agent/auth-profiles.json"
ENV_FILE = BASE_DIR / ".env"
SKILL_DIR = Path.home() / ".openclaw/skills/llm-configurator"
RECIPES_FILE = SKILL_DIR / "recipes.json"
SNAPSHOT_DIR = SKILL_DIR / ".snapshot"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def backup():
    """Creates a snapshot of current working config."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(CONFIG_FILE, SNAPSHOT_DIR / "openclaw.json.bak")
    shutil.copy(AUTH_FILE, SNAPSHOT_DIR / "auth-profiles.json.bak")
    if ENV_FILE.exists():
        shutil.copy(ENV_FILE, SNAPSHOT_DIR / ".env.bak")
    print(f"Snapshot created at {SNAPSHOT_DIR}")

def rollback():
    """Restores from the last known good snapshot."""
    print("Performing emergency rollback...")
    shutil.copy(SNAPSHOT_DIR / "openclaw.json.bak", CONFIG_FILE)
    shutil.copy(SNAPSHOT_DIR / "auth-profiles.json.bak", AUTH_FILE)
    if (SNAPSHOT_DIR / ".env.bak").exists():
        shutil.copy(SNAPSHOT_DIR / ".env.bak", ENV_FILE)
    print("Rollback complete. System restored to previous state.")

def check_health(provider_name, config):
    """Simple HTTP check to see if the provider is reachable."""
    try:
        provider = config['models']['providers'].get(provider_name)
        if not provider:
            return False
        
        url = provider.get('baseUrl')
        if not url:
            return False
        
        if 'google' in provider_name:
            url = url.rstrip('/') + "/models"
        elif 'ollama' in provider_name:
            url = url.replace('/v1', '') + "/api/tags"
        else:
            url = url.rstrip('/') + "/models"

        print(f"Checking health: {url}...")
        
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(url, timeout=5, context=ctx) as response:
                return True
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                print(f"Provider online (received HTTP {e.code} — auth handled at runtime)")
                return True
            raise e
        except urllib.error.URLError as e:
            err_str = str(e)
            if 'SSL' in err_str or 'CERTIFICATE' in err_str:
                print(f"SSL cert verify failed, retrying with insecure context...")
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                try:
                    with urllib.request.urlopen(url, timeout=5, context=ctx) as response:
                        return True
                except urllib.error.HTTPError as e2:
                    if e2.code in (401, 403):
                        print(f"Provider online (received HTTP {e2.code} — auth handled at runtime)")
                        return True
                    raise e2
            elif '403' in err_str or '401' in err_str or 'Forbidden' in err_str or 'Unauthorized' in err_str:
                print(f"Provider online (auth will be handled at runtime)")
                return True
            else:
                print(f"Health check failed: {e}")
                raise e
    except Exception as e:
        print(f"Health check failed: {e}")
    return False

def switch_model(recipe_name):
    recipes = load_json(RECIPES_FILE)
    if recipe_name not in recipes:
        print(f"Error: Recipe '{recipe_name}' not found.")
        sys.exit(1)
    
    recipe = recipes[recipe_name]
    model_id = recipe['id']
    provider_name = recipe['provider']
    overrides = recipe.get('settings', {})

    # 1. Backup current state
    backup()

    # 2. Modify openclaw.json
    config = load_json(CONFIG_FILE)
    
    # Update primary model
    config['agents']['defaults']['model']['primary'] = model_id
    
    # Apply overrides (like reasoning: false)
    if provider_name in config['models']['providers']:
        provider_cfg = config['models']['providers'][provider_name]
        # Find the specific model in the provider list to apply settings
        for m in provider_cfg.get('models', []):
            if m['id'] == model_id.split('/')[-1]:
                m.update(overrides)
    
    save_json(CONFIG_FILE, config)
    print(f"Config updated to {model_id} (Provider: {provider_name})")

    # 3. Health Check with Retries
    max_retries = 3
    for i in range(1, max_retries + 1):
        print(f"Attempt {i}/{max_retries} to verify connectivity...")
        if check_health(provider_name, config):
            print("Connectivity verified! Model switch successful.")
            return True
        else:
            print(f"Attempt {i} failed.")
    
    # 4. Rollback if all attempts fail
    print("Critical: Model unreachable after 3 attempts.")
    rollback()
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python config_manager.py [switch <recipe_name> | rollback]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "switch" and len(sys.argv) == 3:
        success = switch_model(sys.argv[2])
        sys.exit(0 if success else 1)
    elif cmd == "rollback":
        rollback()
        sys.exit(0)
    else:
        print("Invalid command.")
        sys.exit(1)
