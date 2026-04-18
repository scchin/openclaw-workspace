#!/usr/bin/env python3
"""
Google Model Rate Guard — Agent-side integration

Call this BEFORE each Google model API call to check if you need to wait.
Returns: 0 = proceed immediately, N = wait N seconds

Usage:
    python3 rate_guard.py check          # returns wait time to stdout
    python3 rate_guard.py record-call    # record a completed call
    python3 rate_guard.py record-429      # record a 429 hit
    python3 rate_guard.py status         # show current state
    python3 rate_guard.py reset          # reset state
"""

import json
import os
import sys
import time
import ssl
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
STATE_FILE = Path.home() / ".openclaw/hooks/google-model-guard/state.json"
LOG_FILE   = Path.home() / ".openclaw/logs/google-model-guard.log"

# ─── Google Models ─────────────────────────────────────────────────────────────
GOOGLE_MODELS = {"gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemma-4-26b-a4b", "gemini"}

# ─── Config ────────────────────────────────────────────────────────────────────
CONFIG = {
    "targetRpm": 10,
    "warningRpm": 8,
    "backoffDelay": 15,
    "emergencyDelay": 30,
    "emergencyWindow": 120,
    "minInterval": 2.0,
}

# ─── SSL ─────────────────────────────────────────────────────────────────────
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl._create_unverified_context()


# ─── State ───────────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return fresh_state()


def fresh_state() -> dict:
    return {
        "active": False,
        "model": "",
        "rpm": CONFIG["targetRpm"],
        "lastCallTs": 0.0,
        "callTimestamps": [],
        "last429Ts": None,
        "last500Ts": None,
        "consecutive429": 0,
        "consecutive500": 0,
        "intervalSecs": 60 / CONFIG["targetRpm"],
        "status": "normal",
    }


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ─── Logging ────────────────────────────────────────────────────────────────
def log(action: str, **kwargs) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "action": action, **kwargs}) + "\n"
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except Exception:
        pass


# ─── Core Logic ─────────────────────────────────────────────────────────────
def check_wait() -> float:
    """Check if we need to wait before making a call. Returns wait time in seconds."""
    state = load_state()
    if not state["active"]:
        return 0.0

    now = time.time()

    # Prune timestamps older than 60 seconds
    cutoff = now - 60
    state["callTimestamps"] = [t for t in state["callTimestamps"] if t > cutoff]

    current_rpm = len(state["callTimestamps"]) + 1  # +1 for call being added

    # Adaptive interval adjustment
    if state["status"] in ("normal", "warning"):
        if current_rpm > CONFIG["warningRpm"]:
            # Slow down proactively
            new_interval = min(state["intervalSecs"] * 1.2, 15.0)
            if new_interval != state["intervalSecs"]:
                state["intervalSecs"] = new_interval
                log("warning", reason="rpm_approaching_limit", current_rpm=current_rpm,
                    new_interval=new_interval)
                save_state(state)

    # Calculate wait based on interval
    wait = 0.0
    if state["lastCallTs"] > 0:
        elapsed = now - state["lastCallTs"]
        wait = max(0.0, state["intervalSecs"] - elapsed)

    # Cap minimum interval
    wait = max(wait, CONFIG["minInterval"])

    return round(wait, 1)


def record_call() -> dict:
    """Record that a call was made. Returns (wait_seconds_used, new_state)."""
    state = load_state()
    if not state["active"]:
        return {"waitUsed": 0, "state": state}

    now = time.time()
    state["callTimestamps"] = [t for t in state["callTimestamps"] if t > now - 60]
    state["callTimestamps"].append(now)
    state["lastCallTs"] = now
    state["rpm"] = len(state["callTimestamps"])

    # If we were in backoff/emergency, recover to normal after successful call
    if state["status"] in ("backoff", "emergency"):
        state["status"] = "normal"
        state["intervalSecs"] = 60 / CONFIG["targetRpm"]
        state["consecutive429"] = 0
        log("recovered", previousStatus=state["status"])

    save_state(state)
    return {"waitUsed": 0, "state": state}


def record_429() -> dict:
    """Record a 429 error. Returns (wait_seconds, new_state)."""
    state = load_state()
    if not state["active"]:
        return {"waitSecs": 0, "state": state}

    now = time.time()
    state["consecutive429"] += 1
    state["last429Ts"] = now

    # Check if within emergency window
    if state["last429Ts"] and state["consecutive429"] >= 2:
        wait = CONFIG["emergencyDelay"]
        state["status"] = "emergency"
        state["intervalSecs"] = CONFIG["emergencyDelay"]
        log("emergency", reason="consecutive_429", consecutive429=state["consecutive429"], wait=wait)
    else:
        wait = CONFIG["backoffDelay"]
        state["status"] = "backoff"
        state["intervalSecs"] = CONFIG["backoffDelay"]
        log("429", wait=wait, consecutive429=state["consecutive429"])

    save_state(state)
    return {"waitSecs": wait, "state": state}


CONFIG_500 = {
    "backoffDelay": 20,     # seconds to wait on first 500
    "emergencyDelay": 45,   # seconds to wait on second 500 in short time
    "emergencyWindow": 120, # seconds between 500s to trigger emergency mode
}


def record_500() -> dict:
    """Record a 500 INTERNAL error. Returns (wait_seconds, new_state)."""
    state = load_state()
    if not state["active"]:
        return {"waitSecs": 0, "state": state}

    now = time.time()
    state["consecutive500"] = state.get("consecutive500", 0) + 1
    state["last500Ts"] = now

    # Check if within emergency window
    if state.get("last500Ts") and state["consecutive500"] >= 2:
        wait = CONFIG_500["emergencyDelay"]
        state["status"] = "emergency500"
        state["intervalSecs"] = CONFIG_500["emergencyDelay"]
        log("500_emergency", reason="consecutive_500", consecutive500=state["consecutive500"], wait=wait)
    else:
        wait = CONFIG_500["backoffDelay"]
        state["status"] = "backoff500"
        state["intervalSecs"] = CONFIG_500["backoffDelay"]
        log("500", wait=wait, consecutive500=state["consecutive500"])

    save_state(state)
    return {"waitSecs": wait, "state": state}


def activate(model: str) -> dict:
    """Activate guard for a Google model."""
    is_google = any(m in model.lower() for m in GOOGLE_MODELS)
    state = load_state()

    if not is_google:
        if state["active"]:
            log("deactivated", previousModel=state["model"])
        state = fresh_state()
        save_state(state)
        return {"active": False, "state": state}

    state = {
        **fresh_state(),
        "active": True,
        "model": model,
        "rpm": CONFIG["targetRpm"],
        "intervalSecs": 60 / CONFIG["targetRpm"],
    }
    log("activated", model=model, rpm=state["rpm"], interval=state["intervalSecs"])
    save_state(state)
    return {"active": True, "state": state}


def status() -> dict:
    state = load_state()
    now = time.time()
    recent = [t for t in state.get("callTimestamps", []) if t > now - 60]
    return {
        **state,
        "currentRpm": len(recent),
        "config": CONFIG,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    cmd = sys.argv[1]

    if cmd == "check":
        wait = check_wait()
        print(wait)
        return 0

    elif cmd == "record-call":
        result = record_call()
        print(json.dumps(result))
        return 0

    elif cmd == "record-429":
        result = record_429()
        print(json.dumps(result))
        return 0

    elif cmd == "record-500":
        result = record_500()
        print(json.dumps(result))
        return 0

    elif cmd == "status":
        print(json.dumps(status(), indent=2))
        return 0

    elif cmd == "activate":
        model = sys.argv[2] if len(sys.argv) > 2 else "gemma-4-31b-it"
        result = activate(model)
        print(json.dumps(result, indent=2))
        return 0

    elif cmd == "reset":
        save_state(fresh_state())
        log("reset")
        print("State reset.")
        return 0

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
