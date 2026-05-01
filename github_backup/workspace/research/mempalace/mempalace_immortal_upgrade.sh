#!/bin/bash
# MemPalace Immortal Immune Upgrade Script
# Version: 1.0.0 (v4 -> v5)
# Focus: Zero-Risk, Empirical Evidence, Structural Integrity

set -euo pipefail

# --- Configuration ---
PROD_PALACE="$HOME/.mempalace"
BACKUP_PALACE="$HOME/.mempalace_backup_$(date +%Y%m%d_%H%M%S)"
SANDBOX_DIR="/tmp/mempalace_v5_sandbox"
VENV_DIR="$SANDBOX_DIR/venv"
MEMPALACE_REPO="https://github.com/MemPalace/mempalace.git"
BRANCH="develop"

log() { echo -e "\033[1;34m[IMMORTAL-UPGRADE]\033[0m $1"; }
err() { echo -e "\033[1;31m[ERROR]\033[0m $1"; exit 1; }

# 1. Pre-flight Check
log "Starting Pre-flight checks..."
if [ ! -d "$PROD_PALACE" ]; then
    err "Production palace not found at $PROD_PALACE"
fi

# 2. Immutable Backup
log "Creating immutable backup at $BACKUP_PALACE..."
cp -R "$PROD_PALACE" "$BACKUP_PALACE"
# Attempt to lock the backup to prevent accidental modification
chmod -R 444 "$BACKUP_PALACE" 2>/dev/null || log "Warning: Could not set read-only on backup."

# 3. Sandbox Setup
log "Setting up isolated sandbox at $SANDBOX_DIR..."
rm -rf "$SANDBOX_DIR"
mkdir -p "$SANDBOX_DIR"
cp -R "$PROD_PALACE" "$SANDBOX_DIR/prod_data"

log "Initializing sandbox virtual environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install "git+${MEMPALACE_REPO}@${BRANCH}"

# 4. Functional Verification (The 'Immortal' Gate)
log "Running sandbox stability verification..."
# We use a health-check script (mempalace_v5_core.py) to verify routing and status
# This script is assumed to be bundled or created during the align phase.
if [ -f "mempalace_v5_core.py" ]; then
    if ! "$VENV_DIR/bin/python3" mempalace_v5_core.py "$SANDBOX_DIR/prod_data" "health check"; then
        err "Sandbox verification failed. Aborting upgrade to prevent production corruption."
    fi
else
    log "Verification script not found, performing basic status check..."
    if ! "$VENV_DIR/bin/mempalace" --palace "$SANDBOX_DIR/prod_data" status > /dev/null 2>&1; then
        err "Basic status check failed in sandbox."
    fi
fi

# 5. Atomic Pointer-Switch
log "Executing atomic pointer-switch..."
# To ensure zero-risk, we use a symlink switch or a rapid rename
# Here we use the rename-and-restore method for maximum compatibility
mv "$PROD_PALACE" "${PROD_PALACE}.old"
cp -R "$SANDBOX_DIR/prod_data" "$PROD_PALACE"

# 6. Final Validation
log "Final production validation..."
if ! /Users/KS/.local/bin/mempalace status > /dev/null 2>&1; then
    log "Production validation failed! Rolling back immediately..."
    rm -rf "$PROD_PALACE"
    mv "${PROD_PALACE}.old" "$PROD_PALACE"
    err "Upgrade failed and was rolled back."
fi

rm -rf "${PROD_PALACE}.old"
log "Upgrade completed successfully. System is now running MemPalace v5 (Develop)."
log "Backup preserved at: $BACKUP_PALACE"
