# OpenClaw Infrastructure Research - Baseline Mode

## Gateway Layer
### Service Configuration
- **Service Type**: LaunchAgent (loaded)
- **Binary Path**: `/opt/homebrew/opt/node/bin/node`
- **Entry Point**: `/opt/homebrew/lib/node_modules/openclaw/dist/index.js gateway`
- **Port**: `18792` (Defined by `OPENCLAW_GATEWAY_PORT` environment variable)
- **Service File**: `~/Library/LaunchAgents/ai.openclaw.gateway.plist`
- **Config File**: `~/.openclaw/openclaw.json`
- **Logs**: `/tmp/openclaw/openclaw-2026-04-18.log`

### Network & Connectivity
- **Bind Mode**: `loopback` (127.0.0.1)
- **Listening Interfaces**: `192.168.196.11:18792`, `127.0.0.1:18792`
- **Dashboard**: `http://127.0.0.1:18792/`
- **RPC Probe**: OK
- **Version**: 2026.4.15 (041266a)

### Operational Status
- **Runtime PID**: 90312
- **State**: Active
- **Conflict Note**: Gateway runtime PID does not own the listening port. Other gateway process(es) are listening: 77082.

---

## Guardian & Proxy Infrastructure
The system employs a multi-layered proxy architecture to handle authentication, LAN access, and output purification.

### 1. System Guardian (`guardian.py`)
A self-healing monitor that ensures the environment remains consistent.
- **Monitors**: Gateway connectivity (Port 18792) and configuration integrity.
- **Self-Healing Actions**:
    - **Config Patching**: Automatically restores `allowedOrigins` in `openclaw.json`.
    - **Environment Patching**: Fixes API Keys in `ai.openclaw.gateway.plist`.
    - **Key Synchronization**: Ensures `.env`, `models.json`, and `auth-profiles.json` use the same `TARGET_API_KEY`.
- **Recovery**: Uses `launchctl kickstart` to restart the Gateway after applying patches.
- **Event Logging**: Records recovery events to `~/.openclaw/guardian/recovery_event.json`.

### 2. LAN HTTPS Proxy (`lan_https_proxy.py`)
Provides a secure, TLS-encrypted endpoint for remote LAN devices.
- **Role**: TLS Termination Proxy.
- **Binding**: Binds to LAN IPs (e.g., `192.168.196.11:18792`) using `lan_cert.pem` and `lan_key.pem`.
- **Backend**: Forwards decrypted traffic to `127.0.0.1:18789` (Injection Proxy).
- **Optimizations**:
    - **HTTP Keep-Alive**: Maintains TLS connections across multiple HTTP requests to reduce handshake latency.
    - **WebSocket Bridging**: Supports full-duplex bridging for WebSocket traffic.
    - **Header Rewriting**: Recalculates `Content-Length` and manages `Connection` headers to bridge Keep-Alive clients to short-lived backend connections.

### 3. Injection Proxy (`injection_proxy.py`)
The core logic layer for request/response manipulation.
- **Role**: Authentication and Purification Proxy.
- **Binding**: `0.0.0.0:18789`.
- **Request Interception**:
    - **Auth Injection**: Injects `Authorization: Bearer <token>` from `openclaw.json`.
    - **Origin Spoofing**: Overwrites `Origin` and `Host` to `127.0.0.1:18792` to bypass Gateway CORS/AllowedOrigins restrictions.
- **Response Hijacking**:
    - **Global Purification**: Intercepts HTML and JSON responses. Removes LaTeX symbols and replaces them with Unicode equivalents (e.g., \rightarrow -> →) using a mapping table.
    - **JS Injection**: Injects a custom script into HTML <head> or before </body>.
        - **Token Passage**: Appends token to URL hash (#token=...) for frontend authentication.
        - **Control Channel**: Establishes a WebSocket to ws://{LAN_IP}:18790 to receive FORCE_RELOAD commands.
- **Self-Healing Integration**: Detects 429 or 500 errors and triggers a system refresh via http://127.0.0.1:18793/trigger-refresh.

---

## Runtime & OS Interaction
### Runtime Context
- **OS**: Darwin 25.3.0 (arm64)
- **Node**: v25.6.1
- **Shell**: zsh
- **Workspace**: `/Users/KS/.openclaw/workspace`

### Task Management (`system-task-manager`)
- **Implementation**: Python script at `~/.openclaw/skills/system-task-manager/scripts/manager.py`.
- **Purpose**: Persistent tracking of long-running tasks across sessions to ensure recovery after restarts.
- **Actions**: `register`, `update`, `clear`, `list`.

### Process Hierarchy (Partial)
- `openclaw-gateway` (PID 90312)
- `guardian.py` (PID 77084)
- `lan_https_proxy.py` (PID 77082)
- `injection_proxy.py` (PID 77079)
- `ui_proxy.py` (PID 77080)
- `sync_sidecar.py` (PID 77062)
- `rate-limit-proxy/proxy.py` (PID 77083)
