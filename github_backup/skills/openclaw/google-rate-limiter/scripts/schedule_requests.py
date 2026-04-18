#!/usr/bin/env python3
"""
Google Model Request Scheduler
Smart batching & rate-limiting to avoid 429 per-minute quota exhaustion.

Usage:
    # Process a batch of prompts with automatic rate limiting
    python3 schedule_requests.py --prompts "Hello|What is AI?|Tell me a joke" --interval 6

    # From file (one prompt per line)
    python3 schedule_requests.py --file prompts.txt --interval 6

    # With adaptive rate control (slow down when hitting 429)
    python3 schedule_requests.py --prompts "Q1|Q2|Q3|Q4|Q5" --interval 5 --adaptive

Interval = seconds between each request. 6s interval ≈ 10 requests/minute (safe zone).
"""

import argparse
import os
import sys
import time
import json
import ssl
import urllib.request
import urllib.error
from datetime import datetime
from collections import deque


# ─── SSL Context (Mac fix) ───────────────────────────────────────────────────
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CONTEXT = ssl._create_unverified_context()


# ─── Google API Call ─────────────────────────────────────────────────────────
def call_google_model(model: str, prompt: str, api_key: str = None, max_tokens: int = 150) -> dict:
    if api_key is None:
        api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return {"success": False, "error": {"message": "No API key found. Set GOOGLE_API_KEY env."}, "status_code": 401}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7}
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30, context=SSL_CONTEXT) as response:
            return {"success": True, "data": json.loads(response.read().decode("utf-8"))}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
        except json.JSONDecodeError:
            error_json = {"error": {"message": error_body}}
        return {"success": False, "error": error_json, "status_code": e.code}
    except Exception as e:
        return {"success": False, "error": {"message": str(e)}, "status_code": None}


def is_rate_limit_error(result: dict) -> bool:
    if not result.get("success") and result.get("status_code") == 429:
        return True
    error = result.get("error", {})
    if isinstance(error, dict):
        status = error.get("status", "")
        code = error.get("code", 0)
        message = str(error.get("message", "")).lower()
        if status in ("RESOURCE_EXHAUSTED", "rateLimitExceeded") or code == 429 or \
           "exhausted" in message or "rate limit" in message or "quota" in message:
            return True
    return False


def format_response(result: dict) -> str:
    try:
        candidates = result.get("data", {}).get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if part.get("text") and part.get("thought") is not True:
                    return part["text"]
            if parts:
                return parts[-1].get("text", "[no text]")
        return "[no response]"
    except Exception:
        return "[parse error]"


# ─── Rate Limiter ────────────────────────────────────────────────────────────
class RateLimiter:
    """Tracks RPM and optionally slows down when 429 hits."""

    def __init__(self, target_rpm: int = 10, adaptive: bool = True):
        # target_rpm: safe zone is ~10-12, burst up to 15-20 but risky
        self.target_rpm = target_rpm
        self.adaptive = adaptive
        self.request_times = deque()
        self.current_interval = 60.0 / target_rpm  # seconds per request
        self.min_interval = 2.0   # never faster than this
        self.max_interval = 60.0   # never slower than this
        self.backoff_multiplier = 1.0
        self.total_requests = 0
        self.total_429 = 0

    def tick(self) -> float:
        """Wait the appropriate interval between requests."""
        now = time.time()

        # Prune timestamps older than 60 seconds
        cutoff = now - 60.0
        while self.request_times and self.request_times[0] < cutoff:
            self.request_times.popleft()

        # Current actual RPM
        actual_rpm = len(self.request_times)

        # Adaptive: if we're already at high RPM, slow down proactively
        if self.adaptive and actual_rpm >= self.target_rpm:
            self.current_interval = min(self.current_interval * 1.2, self.max_interval)
        elif self.adaptive and actual_rpm <= self.target_rpm * 0.5:
            self.current_interval = max(self.current_interval * 0.9, self.min_interval)

        if self.request_times:
            elapsed = now - self.request_times[-1]
            wait = max(0, self.current_interval - elapsed)
            time.sleep(wait)

        self.request_times.append(time.time())
        self.total_requests += 1
        return self.current_interval

    def on_429(self):
        """Called when a 429 is hit — slow down significantly."""
        self.total_429 += 1
        if self.adaptive:
            self.current_interval = min(self.current_interval * 2.5, self.max_interval)
            next_expected_rpm = 60.0 / self.current_interval
            print(f"   ⚠️  [Adaptive] 429 hit! Slowing to ~{next_expected_rpm:.1f} RPM (interval={self.current_interval:.1f}s)")


# ─── Scheduler ────────────────────────────────────────────────────────────────
def process_prompts(prompts: list, args) -> None:
    limiter = RateLimiter(target_rpm=args.rpm, adaptive=args.adaptive)

    print(f"\n📦 Scheduling {len(prompts)} prompts at ~{args.rpm} RPM (interval={60/args.rpm:.1f}s)")
    if args.adaptive:
        print("   Adaptive mode: ON (will slow down on 429)")
    print(f"   Model: {args.model}")
    print("-" * 60)

    results = []
    for i, prompt in enumerate(prompts, 1):
        actual_interval = limiter.tick()

        print(f"\n[{i}/{len(prompts)}] ({datetime.now().strftime('%H:%M:%S')}) ", end="", flush=True)
        print(f"Interval: {actual_interval:.1f}s | Accumulated RPM: {len(limiter.request_times)}")

        result = call_google_model(args.model, prompt, max_tokens=args.max_tokens)

        if result["success"]:
            response = format_response(result)
            usage = result.get("data", {}).get("usageMetadata", {})
            print(f"   ✅ ({usage.get('promptTokenCount',0)}→{usage.get('candidatesTokenCount',0)} tok) {response}")
            results.append({"prompt": prompt, "response": response, "status": "ok"})
        else:
            error_msg = result.get("error", {}).get("message", str(result.get("error")))
            if is_rate_limit_error(result):
                limiter.on_429()
                print(f"   ⚠️  429 — backing off, will continue next cycle")
                # Save this prompt to retry at end
                results.append({"prompt": prompt, "response": error_msg, "status": "rate_limited"})
            else:
                print(f"   ❌ {error_msg[:80]}")
                results.append({"prompt": prompt, "response": error_msg, "status": "error"})

        # Brief pause to let system breathe
        if args.pause and i < len(prompts):
            time.sleep(args.pause)

    # Retry 429-failed items ONCE at the end
    retries = [r for r in results if r["status"] == "rate_limited"]
    if retries:
        print(f"\n🔁 Retrying {len(retries)} rate-limited prompt(s) after cooldown...")
        time.sleep(20)  # Give quota time to recover
        for r in retries:
            print(f"\n[RETRY] {r['prompt'][:50]}...")
            result = call_google_model(args.model, r["prompt"], max_tokens=args.max_tokens)
            if result["success"]:
                r["response"] = format_response(result)
                r["status"] = "ok"
                print(f"   ✅ {r['response']}")
            else:
                print(f"   ❌ {result.get('error',{}).get('message','failed')[:80]}")

    # ─── Summary ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print(f"   Total requests : {limiter.total_requests}")
    print(f"   429 hits       : {limiter.total_429}")
    print(f"   Success        : {sum(1 for r in results if r['status']=='ok')}")
    print(f"   Failed         : {sum(1 for r in results if r['status'] not in ('ok',))}")
    ok_rate = (sum(1 for r in results if r['status']=='ok') / len(results) * 100) if results else 0
    print(f"   Success rate   : {ok_rate:.0f}%")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"   Output saved to: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Smart Google Model Request Scheduler")
    parser.add_argument("--prompts", help="Prompts separated by pipe '|' character")
    parser.add_argument("--file", help="File with one prompt per line")
    parser.add_argument("--model", default="gemma-4-31b-it")
    parser.add_argument("--rpm", type=int, default=10, help="Target requests per minute (default: 10, safe)")
    parser.add_argument("--interval", type=float, help="Override interval in seconds (overrides --rpm)")
    parser.add_argument("--adaptive", action="store_true", help="Auto-adjust rate on 429 hits")
    parser.add_argument("--max-tokens", type=int, default=150)
    parser.add_argument("--pause", type=float, default=0.5, help="Pause between requests (default: 0.5s)")
    parser.add_argument("--api-key", help="Google API Key (or set GOOGLE_API_KEY env)")
    parser.add_argument("--output", help="Save results to JSON file")

    args = parser.parse_args()

    if args.interval:
        args.rpm = int(60 / args.interval)

    if args.prompts:
        prompts = [p.strip() for p in args.prompts.split("|") if p.strip()]
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
    else:
        print("Error: provide --prompts or --file")
        return 1

    if not prompts:
        print("No prompts found.")
        return 1

    process_prompts(prompts, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
