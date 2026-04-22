#!/bin/bash
# OpenClaw 區域網路自癒修復指令 (Manual Trigger v1.0)
# 作用：強制同步所有金鑰、環境變數與安全白名單，確保系統更新後能一鍵恢復。

echo "🔧 啟動 OpenClaw 區域網路自癒修復程序..."

# 1. 執行 Guardian v4.0 的自癒熱修補
echo "📦 正在檢查並修補 .plist 環境變數與 JSON 設定..."
python3 /Users/KS/.openclaw/guardian/guardian.py --once

# 2. 強制重啟所有連動服務
echo "🚀 正在重新啟動核心服務鏈..."
uid=$(id -u)
launchctl kickstart -k gui/$uid/ai.openclaw.gateway.v2
launchctl kickstart -k gui/$uid/com.openclaw.lan-https-proxy
launchctl kickstart -k gui/$uid/com.openclaw.injection-proxy

echo "✅ [完成] 區域網路 HTTPS 與 自動登入功能已成功恢復。"
echo "👉 您現在可以重新開啟瀏覽器連線：https://192.168.196.11:18792/"
