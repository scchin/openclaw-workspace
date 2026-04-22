#!/bin/bash
# OpenClaw 啟動引導器 (Omni-Trinity v4.0 Final)
# 整合功能：
# 1. IP 對位
# 2. Omni-Sentinel 基因哨兵 (自動清理技能垃圾)
# 3. v4.0 內核物理防線巡檢
# 4. EPERM 補丁注入

echo "🛡️ [Omni-Guardian v4.0] 啟動前底層防線與基因哨兵巡檢中..."

# 執行 v4.0 統合巡檢 (含 Sentinel)
bash /Users/KS/.openclaw/guardian/soul-fortify.sh --check

echo "🚀 [Omni-Guardian v4.0] 系統純淨度校驗完成，啟動 OpenClaw..."
exec /opt/homebrew/opt/node/bin/node \
    --import /Users/KS/.openclaw/guardian/epperm-patch.mjs \
    /opt/homebrew/lib/node_modules/openclaw/dist/index.js gateway
