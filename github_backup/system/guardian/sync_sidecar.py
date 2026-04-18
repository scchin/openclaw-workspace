#!/usr/bin/env python3
import asyncio
import json
import time
import os
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import websockets

# 配置
PORT = 18790
HTTP_PORT = 18793
GATEWAY_URL = "http://127.0.0.1:18789/api/dialogue"


# 儲存所有已連接的 WebSocket 用戶端
CONNECTED_CLIENTS = set()
# 全域 loop 供 HTTP 線程使用
loop = None

# --- WebSocket 處理邏輯 ---
async def ws_handler(websocket):
    CONNECTED_CLIENTS.add(websocket)
    print(f"🌐 UI Client connected. Total: {len(CONNECTED_CLIENTS)}")
    try:
        async for message in websocket:
            pass 
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        print(f"🌐 UI Client disconnected. Total: {len(CONNECTED_CLIENTS)}")

async def notify_all_clients():
    if not CONNECTED_CLIENTS:
        print("⚠️ No UI clients connected to notify.")
        return
    
    print(f"📢 Sending FORCE_RELOAD to {len(CONNECTED_CLIENTS)} clients...")
    await asyncio.gather(
        *[client.send("FORCE_RELOAD") for client in CONNECTED_CLIENTS],
        return_exceptions=True
    )

# --- HTTP 處理邏輯 ---
class SidecarHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/sync":
            try:
                with urllib.request.urlopen(GATEWAY_URL, timeout=2) as resp:
                    current_state = json.loads(resp.read().decode())
            except Exception:
                current_state = {"status": "Syncing...", "last_update": time.time()}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(current_state).encode())
        elif self.path == "/version":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            code_mtime = os.path.getmtime(__file__)
            version_id = f"v{int(time.time())}_{int(code_mtime)}"
            self.wfile.write(json.dumps({"version": version_id, "status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/trigger-refresh":
            print("🚨 Received trigger-refresh request! Notifying clients...")
            if loop:
                asyncio.run_coroutine_threadsafe(notify_all_clients(), loop)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "refresh_pushed"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

def run_http_server():
    server = HTTPServer(("127.0.0.1", HTTP_PORT), SidecarHTTPHandler)
    print(f"🌐 HTTP Sync Sidecar running on port {HTTP_PORT}...")
    server.serve_forever()


async def main():
    global loop
    loop = asyncio.get_running_loop()
    
    # 啟動 HTTP 伺服器線程
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    print(f"🚀 WebSocket Push Sidecar starting on ws://127.0.0.1:{PORT}...")
    async with websockets.serve(ws_handler, "127.0.0.1", PORT):
        await asyncio.Future() # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
