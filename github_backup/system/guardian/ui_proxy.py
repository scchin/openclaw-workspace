#!/usr/bin/env python3
# 版本：1.1（2026-04-18）
# 變更：開放區域網路存取
#   - HTTPServer 綁定由 127.0.0.1 改為 0.0.0.0
#   - 新增 get_lan_ip() 動態取得區網 IP
#   - 注入 JS 改為用動態區網 IP，修正遠端瀏覽器 sync/reload 失效問題
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import socket

LISTEN_PORT = 18791
TARGET_PORT = 18789

def get_lan_ip():
    """動態取得本機對外的區網 IP，供注入 JS 使用"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LAN_IP = get_lan_ip()

# 注入的 JS 腳本：實現靜默更新 + 500 錯誤一鍵恢復
INJECTED_JS = """
<script>
(function() {
    console.log("🛡️ OpenClaw Reliability Client Injected");

    // 1. 靜默同步邏輯
    setInterval(async () => {
        try {
            const resp = await fetch('http://{LAN_IP_PLACEHOLDER}:18790/sync');
            const data = await resp.json();
            if (data.delta && Object.keys(data.delta).length > 0) {
                console.log("✨ Silent Update Received:", data.delta);
            }
        } catch (e) {
            console.error("Sync failed", e);
        }
    }, 10000);

    // 2. 500 錯誤自動檢測與一鍵恢復 (Scheme C)
    const style = document.createElement('style');
    style.innerHTML = `
        .oc-retry-btn {
            background: #ff4d4f;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 12px;
            margin: 8px 0;
            cursor: pointer;
            font-weight: bold;
            font-size: 12px;
            transition: background 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .oc-retry-btn:hover { background: #ff7875; }
        .oc-retry-btn:active { background: #d9363e; }
    `;
    document.head.appendChild(style);

    const observer = new MutationObserver(() => {
        const bodyText = document.body.innerText;
        if (bodyText.includes("LLM error") && bodyText.includes("500")) {
            // 尋找包含錯誤訊息的元素
            const elements = document.querySelectorAll('*');
            for (let el of elements) {
                if (el.children.length === 0 && el.innerText.includes("LLM error") && el.innerText.includes("500")) {
                    if (!el.parentElement.querySelector('.oc-retry-btn')) {
                        const btn = document.createElement('button');
                        btn.className = 'oc-retry-btn';
                        btn.innerHTML = '🔄 立即恢復 (Retry Now)';
                        btn.onclick = () => {
                            console.log("🚀 Triggering Fast Recovery...");
                            location.reload(); // 最可靠的恢復方式：重新初始化狀態
                        };
                        el.parentElement.insertBefore(btn, el.nextSibling);
                        console.log("✅ Recovery button injected");
                    }
                }
            }
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
"""

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = f"http://127.0.0.1:{TARGET_PORT}{self.path}"
        try:
            with urllib.request.urlopen(url) as resp:
                content_type = resp.getheader("Content-Type", "")
                data = resp.read()

                self.send_response(resp.getcode())
                for header, value in resp.getheaders():
                    self.send_header(header, value)
                self.end_headers()

                if "text/html" in content_type:
                    # 在 </body> 前注入 JS，並將 placeholder 替換為真實區網 IP
                    html = data.decode('utf-8', errors='ignore')
                    js_to_inject = INJECTED_JS.replace("{LAN_IP_PLACEHOLDER}", LAN_IP)
                    if "</body>" in html:
                        html = html.replace("</body>", f"{js_to_inject}</body>")
                    else:
                        html += js_to_inject
                    self.wfile.write(html.encode())
                else:
                    self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Proxy Error: {e}".encode())

if __name__ == "__main__":
    print(f"🌐 UI Injector Proxy running on port {LISTEN_PORT} (0.0.0.0 - LAN enabled)")
    print(f"👉 本機存取：http://127.0.0.1:{LISTEN_PORT}")
    print(f"👉 區網存取：http://{LAN_IP}:{LISTEN_PORT}")
    HTTPServer(("0.0.0.0", LISTEN_PORT), ProxyHandler).serve_forever()
