#!/usr/bin/env python3
# 版本：2.0（2026-04-18）
# 功能：OpenClaw LAN HTTPS 終端代理（HTTP/1.1 Keep-Alive 版）
#
# v1.0 的根本缺陷：
#   - 將整個 TLS 連線做一個原始 TCP 橋接到 injection_proxy
#   - injection_proxy 每次回應後就關閉連線
#   - LAN 裝置需要為每個資源（JS bundle、CSS、API）重做 TLS 握手
#   - Wi-Fi 延遲下會 timeout → 空白頁
#
# v2.0 修復：
#   - 每個 HTTP 請求各自建立一條新的到 injection_proxy 的 TCP 連線
#   - TLS 連線保持 Keep-Alive，可承載多個 HTTP 請求
#   - 正確解碼 chunked transfer encoding，加回 Content-Length
#   - WebSocket Upgrade 正確橋接（支援聊天室）
#   - 強制 HTTP/1.1（ALPN），避免 HTTP/2 造成浏覽器解析錯誤

import asyncio
import ssl
import os

TARGET_HOST = "0.0.0.0"
TARGET_PORT = 18789          # injection_proxy（物理清洗與強效攔截層）

CERT_FILE = os.path.expanduser("~/.openclaw/guardian/lan_cert.pem")
KEY_FILE  = os.path.expanduser("~/.openclaw/guardian/lan_key.pem")

LAN_BINDINGS = [
    ("127.0.0.1", 18792),
    ("192.168.196.11", 18792),
]

# ─── 工具函數 ─────────────────────────────────────────────────────────────────

def get_content_length(headers: str):
    for line in headers.split("\r\n"):
        if line.lower().startswith("content-length:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except Exception:
                pass
    return None

def is_chunked_encoding(headers: str) -> bool:
    for line in headers.split("\r\n"):
        if line.lower().startswith("transfer-encoding:") and "chunked" in line.lower():
            return True
    return False

async def bridge(reader, writer):
    """單向原始位元組橋接，用於 WebSocket"""
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def read_body(reader, headers: str) -> bytes:
    """根據 Content-Length 或 chunked encoding 讀取完整 HTTP body"""
    cl = get_content_length(headers)
    chunked = is_chunked_encoding(headers)

    if cl is not None:
        if cl == 0:
            return b""
        return await asyncio.wait_for(reader.readexactly(cl), timeout=60.0)

    if chunked:
        body = b""
        while True:
            size_line = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=10.0)
            chunk_size = int(size_line.strip(), 16)
            if chunk_size == 0:
                await reader.readuntil(b"\r\n")  # 最後的 CRLF
                break
            chunk = await asyncio.wait_for(reader.readexactly(chunk_size), timeout=30.0)
            body += chunk
            await reader.readuntil(b"\r\n")  # 每個 chunk 的尾端 CRLF
        return body

    # 沒有 Content-Length 也沒有 chunked：讀到連線關閉為止
    body = b""
    try:
        while True:
            chunk = await asyncio.wait_for(reader.read(65536), timeout=5.0)
            if not chunk:
                break
            body += chunk
    except asyncio.TimeoutError:
        pass
    return body

# ─── 核心：單一 HTTP 請求處理 ─────────────────────────────────────────────────

async def handle_one_request(client_reader, client_writer) -> bool:
    """
    處理一個 HTTP 請求。
    回傳 True  → 繼續 keep-alive，等待下一個請求
    回傳 False → 關閉 TLS 連線
    """
    # 讀取請求 headers
    try:
        req_headers_raw = await asyncio.wait_for(
            client_reader.readuntil(b"\r\n\r\n"), timeout=30.0
        )
    except asyncio.TimeoutError:
        return False
    except Exception:
        return False

    req_headers_text = req_headers_raw.decode("utf-8", errors="ignore")
    is_ws = "upgrade: websocket" in req_headers_text.lower()

    # 讀取請求 body（POST/PUT 等）
    req_body = b""
    cl = get_content_length(req_headers_text)
    if cl and cl > 0:
        try:
            req_body = await asyncio.wait_for(
                client_reader.readexactly(cl), timeout=10.0
            )
        except Exception:
            return False

    # 為這個請求建立一條新的到 injection_proxy 的 TCP 連線
    try:
        srv_reader, srv_writer = await asyncio.open_connection(TARGET_HOST, TARGET_PORT)
    except Exception:
        return False

    # 轉發請求
    srv_writer.write(req_headers_raw + req_body)
    await srv_writer.drain()

    if is_ws:
        # WebSocket：讀取 101 Switching Protocols 回應後，進入全雙工橋接
        try:
            ws_resp_raw = await asyncio.wait_for(
                srv_reader.readuntil(b"\r\n\r\n"), timeout=30.0
            )
            client_writer.write(ws_resp_raw)
            await client_writer.drain()
        except Exception:
            srv_writer.close()
            return False
        # 全雙工橋接剩下的 WebSocket 流量
        await asyncio.gather(
            bridge(client_reader, srv_writer),
            bridge(srv_reader, client_writer),
        )
        srv_writer.close()
        return False  # WebSocket 結束後關閉 TLS

    # 讀取回應 headers
    try:
        resp_headers_raw = await asyncio.wait_for(
            srv_reader.readuntil(b"\r\n\r\n"), timeout=30.0
        )
    except Exception:
        srv_writer.close()
        return False

    resp_headers_text = resp_headers_raw.decode("utf-8", errors="ignore")
    server_wants_close = "connection: close" in resp_headers_text.lower()

    # 讀取完整回應 body
    try:
        resp_body = await read_body(srv_reader, resp_headers_text)
    except Exception:
        resp_body = b""
    finally:
        try:
            srv_writer.close()
        except Exception:
            pass

    # 重寫回應 headers：移除 transfer-encoding 和舊的 content-length，加入正確的值
    cleaned = []
    for line in resp_headers_text.split("\r\n"):
        if not line:
            continue
        ll = line.lower()
        if (ll.startswith("transfer-encoding:")
                or ll.startswith("content-length:")
                or ll.startswith("connection:")):
            continue
        cleaned.append(line)

    cleaned.append(f"Content-Length: {len(resp_body)}")
    cleaned.append("Connection: keep-alive" if not server_wants_close else "Connection: close")

    final_resp = "\r\n".join(cleaned) + "\r\n\r\n"
    client_writer.write(final_resp.encode() + resp_body)
    await client_writer.drain()

    return not server_wants_close

# ─── 主入口：每條 TLS 連線複用多個 HTTP 請求 ────────────────────────────────

async def handle_client(client_reader, client_writer):
    """
    每條 TLS 連線可承載多個 HTTP 請求（Keep-Alive）
    injection_proxy 仍為每個請求各開各關，但 TLS 連線不再中斷
    """
    try:
        while True:
            keep_alive = await handle_one_request(client_reader, client_writer)
            if not keep_alive:
                break
    except Exception:
        pass
    finally:
        try:
            client_writer.close()
            await client_writer.wait_closed()
        except Exception:
            pass

async def main():
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print(f"❌ 憑證不存在，請先執行 mkcert 生成憑證")
        return

    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    # 強制 HTTP/1.1，避免瀏覽器協商 HTTP/2 導致 injection_proxy 解析失敗
    try:
        ssl_ctx.set_alpn_protocols(["http/1.1"])
    except Exception:
        pass

    servers = []
    for (host, port) in LAN_BINDINGS:
        try:
            server = await asyncio.start_server(
                handle_client, host, port, ssl=ssl_ctx
            )
            servers.append(server)
            print(f"✅ HTTPS Keep-Alive 監聽：https://{host}:{port}/")
        except Exception as e:
            print(f"⚠️  無法綁定 {host}:{port} → {e}")

    if not servers:
        print("❌ 所有綁定均失敗。")
        return

    print(f"🔒 OpenClaw LAN HTTPS Proxy v2.0 (Keep-Alive) 就緒")
    print(f"   TLS 終端 → {TARGET_HOST}:{TARGET_PORT} (injection_proxy)")
    print(f"   本機存取（不受影響）：http://127.0.0.1:18791/")

    async def run_server(s):
        async with s:
            await s.serve_forever()

    await asyncio.gather(*[run_server(s) for s in servers])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
