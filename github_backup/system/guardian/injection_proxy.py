#!/usr/bin/env python3
# 版本：4.8（2026-04-18）
# 變更：開放區域網路存取（LAN Support）
#   - asyncio.start_server 綁定由 127.0.0.1 改為 0.0.0.0
#   - 新增 get_lan_ip() 動態取得區網 IP
#   - JS_TEMPLATE 中的 WebSocket URL 改為動態注入區網 IP
#     以修正遠端瀏覽器 ws://127.0.0.1:18790 指向自己而失效的問題
"""
OpenClaw Dual-Mode Injection Proxy (HTTP + WebSocket) - v4.8
The "LAN-Ready" Edition.

Fixes:
1. Removed 'aiohttp' dependency.
2. Enhanced WebSocket Bridge.
3. State-Force Injection.
4. Response Hijacking.
5. Request Interception.
6. DOM Erasure.
7. GLOBAL PURIFICATION: Intercepts and cleans LaTeX symbols from BOTH HTML and JSON responses.
8. LAN Support: Binds to 0.0.0.0, dynamically injects LAN IP into WebSocket JS.
"""

import asyncio
import json
import os
import socket
import urllib.request
import re
from concurrent.futures import ThreadPoolExecutor

# ─── 配置 ────────────────────────────────────────────────────────────────────
LISTEN_PORT = 18789
TARGET_PORT = 18792
TARGET_HOST = "127.0.0.1"
AUTH_FILE = os.path.expanduser("~/.openclaw/openclaw.json")
REFRESH_ENDPOINT = "http://127.0.0.1:18793/trigger-refresh"

def get_lan_ip():
    """動態取得本機對外的區網 IP，供注入 JS WebSocket URL 使用"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LAN_IP = get_lan_ip()

# 物理清洗映射表 (優先處理長符號，覆蓋所有常見 LaTeX 箭頭與數學符號)
SYMBOL_MAP = {
    "\\\\longrightarrow": "→",
    "\\\\rightarrow": "→",
    "\\\\Rightarrow": "⇒",
    "\\\\leftrightarrow": "↔",
    "\\\\Leftrightarrow": "⇔",
    "\\\\downarrow": "↓",
    "\\\\uparrow": "↑",
    "\\\\approx": "≈",
    "\\\\neq": "≠",
    "\\\\le": "≤",
    "\\\\ge": "≥",
    "\\\\pm": "±",
    "\\\\infty": "∞",
    "→": "→",
    "↓": "↓",
    "↑": "↑",
    "≈": "≈",
}

executor = ThreadPoolExecutor(max_workers=5)

JS_TEMPLATE = """
<script>
(function() {{
    const TOKEN = "{token}";
    if (!TOKEN) return;

    console.log('%c[OpenClaw-LAN v5] 啟動原生 token 注入模式...', 'color:#0ff;font-weight:bold');

    // 使用 OpenClaw 原生支援的 URL Hash Token 驗證機制！
    // 透過在 React 載入前把 #token= 掛到 URL 末端，讓 OpenClaw 自己的程式碼去完美處理 
    // localStorage 寫入和 WebSocket 認證，完全避免攔截和狀態衝突！
    if (window.location.hash.indexOf('token=') === -1) {{
        let newHash = window.location.hash;
        if (newHash && newHash.length > 1) {{
            newHash += '&token=' + TOKEN;
        }} else {{
            newHash = '#token=' + TOKEN;
        }}
        // 用 replaceState 變更 URL 但不觸發重新整理，讓後續載入的 React 能夠讀到
        window.history.replaceState(null, '', window.location.pathname + window.location.search + newHash);
        console.log('[LAN-v5] 已將 Token 附加至 URL fragment。');
    }}

    // ── Guardian WS（僅 HTTP 模式）──────────────────────────────────────────
    function connect() {{
        if (location.protocol === 'https:') return;
        const ws = new WebSocket('ws://{LAN_IP_PLACEHOLDER}:18790');
        ws.onmessage = (evt) => {{ if (evt.data === 'FORCE_RELOAD') window.location.reload(true); }};
        ws.onclose = () => setTimeout(connect, 5000);
    }}
    connect();
}})();
</script>
"""



def purify_content(text):
    """物理清洗函數：強制根除 LaTeX 符號並轉換為純 Unicode 符號"""
    if not text or not isinstance(text, str):
        return text
    
    # 1. 處理 LaTeX 環境 (如 \begin{equation} ... \end{equation})
    text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', lambda m: m.group(0).replace('\\begin{', '').replace('\\end{', '').replace('}', ''), text, flags=re.DOTALL)
    
    # 2. 處理 \text{...}
    text = re.sub(r'\\text\{([^}]*)\}', r'\1', text)
    
    # 3. 處理 $...$ 和 $$...$$ 塊 (移除美元符號，但保留內容以進行符號替換)
    text = text.replace('$$', '').replace('$', '')
    
    # 4. 根據映射表替換 (先長後短)
    sorted_symbols = sorted(SYMBOL_MAP.keys(), key=len, reverse=True)
    for symbol in sorted_symbols:
        text = text.replace(symbol, SYMBOL_MAP[symbol])
    
    # 5. 移除殘留 LaTeX 指令 (如 \alpha, \beta)
    text = re.sub(r'\\([a-zA-Z]+)', ' ', text)
    
    # 6. 移除殘留的 LaTeX 大括號 { }
    text = text.replace('{', '').replace('}', '')
    
    # 7. 最終修剪空白
    text = re.sub(r' +', ' ', text).strip()
    
    return text

def purify_json_recursive(data):
    """遞迴清洗 JSON 結構中的所有字串"""
    if isinstance(data, dict):
        return {k: purify_json_recursive(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [purify_json_recursive(item) for item in data]
    elif isinstance(data, str):
        return purify_content(data)
    else:
        return data

def get_gateway_token():
    try:
        with open(AUTH_FILE, "r") as f:
            config = json.load(f)
            return config.get("gateway", {}).get("auth", {}).get("token")
    except Exception:
        return None

def sync_refresh_call():
    try:
        with urllib.request.urlopen(REFRESH_ENDPOINT, timeout=2.0) as resp:
            return resp.status
    except Exception as e:
        return str(e)

async def trigger_refresh():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, sync_refresh_call)
    print(f"🔄 [SelfHealing] 偵測到錯誤，已觸發全域刷新: {result}")

async def bridge(reader, writer):
    try:
        while True:
            data = await reader.read(8192)
            if not data: break
            writer.write(data)
            await writer.drain()
    except Exception: pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except: pass

async def handle_client(client_reader, client_writer):
    try:
        header_data = await asyncio.wait_for(client_reader.readuntil(b"\r\n\r\n"), timeout=5.0)
    except Exception:
        client_writer.close()
        return

    header_text = header_data.decode('utf-8', errors='ignore')
    lines = header_text.split("\r\n")
    request_line = lines[0]
    headers = lines[1:]
    is_websocket = any("upgrade: websocket" in line.lower() for line in headers)
    
    try:
        server_reader, server_writer = await asyncio.open_connection(TARGET_HOST, TARGET_PORT)
    except Exception as e:
        client_writer.write(f"HTTP/1.1 502 Bad Gateway\r\n\r\nProxy Error: {e}".encode())
        await client_writer.drain()
        client_writer.close()
        return

    token = get_gateway_token()
    clean_headers = []
    for line in headers:
        if not line: continue
        lline = line.lower()
        if lline.startswith("authorization:") or lline.startswith("accept-encoding:"): continue
        # 移除 origin/host，稍後以本機值覆寫（解決 Gateway allowedOrigins 封鎖問題）
        if lline.startswith("origin:") or lline.startswith("host:"): continue
        clean_headers.append(line)
    
    if token:
        clean_headers.append(f"Authorization: Bearer {token}")
    # 覆寫 Origin/Host → 讓 Gateway 永遠看到本機請求，對應 gateway.controlUi.allowedOrigins
    clean_headers.append(f"Origin: http://127.0.0.1:{TARGET_PORT}")
    clean_headers.append(f"Host: 127.0.0.1:{TARGET_PORT}")

    final_request = request_line + "\r\n" + "\r\n".join(clean_headers) + "\r\n\r\n"
    server_writer.write(final_request.encode())
    await server_writer.drain()

    if is_websocket:
        await asyncio.gather(bridge(client_reader, server_writer), bridge(server_reader, client_writer))
    else:
        if "POST" in request_line or "PUT" in request_line:
            content_length = 0
            for line in headers:
                if line.lower().startswith("content-length:"):
                    try: content_length = int(line.split(":")[1].strip())
                    except: pass
            if content_length > 0:
                try:
                    body = await asyncio.wait_for(client_reader.readexactly(content_length), timeout=2.0)
                    server_writer.write(body)
                    await server_writer.drain()
                except: pass

        try:
            resp_header_data = await asyncio.wait_for(server_reader.readuntil(b"\r\n\r\n"), timeout=5.0)
            resp_headers_text = resp_header_data.decode('utf-8', errors='ignore')
            
            if "429 Too Many Requests" in resp_headers_text or "500 Internal Server Error" in resp_headers_text:
                asyncio.create_task(trigger_refresh())
            
            modified_resp_headers = []
            for line in resp_headers_text.split("\r\n"):
                if not line: continue
                lline = line.lower()
                if lline.startswith("content-length:") or lline.startswith("transfer-encoding:"): continue
                if lline.startswith("content-security-policy:"): continue
                modified_resp_headers.append(line)
            
            modified_resp_headers.append("Cache-Control: no-cache, no-store, must-revalidate")
            final_resp_headers = "\r\n".join(modified_resp_headers) + "\r\n\r\n"
            
            is_html = "text/html" in resp_headers_text.lower()
            is_json = "application/json" in resp_headers_text.lower()
            
            body = b""
            try:
                while True:
                    chunk = await asyncio.wait_for(server_reader.read(8192), timeout=1.0)
                    if not chunk: break
                    body += chunk
                    if is_html and b"</body>" in body: break
                    if is_json and body.strip().endswith(b"}"): break
            except asyncio.TimeoutError:
                pass

            if is_html:
                try:
                    decoded_body = body.decode('utf-8', errors='ignore')
                    if "API rate limit reached" in decoded_body or "Internal error" in decoded_body:
                        asyncio.create_task(trigger_refresh())
                    decoded_body = purify_content(decoded_body)
                    js_content = JS_TEMPLATE.format(
                        token=token if token else "",
                        LAN_IP_PLACEHOLDER=LAN_IP,
                    )
                    if "<head>" in decoded_body:
                        decoded_body = decoded_body.replace("<head>", f"<head>{js_content}", 1)
                    elif "</body>" in decoded_body:
                        decoded_body = decoded_body.replace("</body>", f"{js_content}</body>")
                    else:
                        decoded_body += js_content
                    body = decoded_body.encode('utf-8')
                except Exception: pass
            elif is_json:
                try:
                    data = json.loads(body.decode('utf-8', errors='ignore'))
                    purified_data = purify_json_recursive(data)
                    body = json.dumps(purified_data, ensure_ascii=False).encode('utf-8')
                except Exception: pass
            
            client_writer.write(final_resp_headers.encode() + body)
            await client_writer.drain()
        except Exception:
            pass
        finally:
            client_writer.close()
            server_writer.close()

async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", LISTEN_PORT)
    print(f"🚀 OpenClaw Dual-Mode Proxy v4.8 listening on 0.0.0.0:{LISTEN_PORT} (LAN enabled)")
    print(f"👉 本機存取：http://127.0.0.1:{LISTEN_PORT}")
    print(f"👉 區網存取：http://{LAN_IP}:{LISTEN_PORT}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass
