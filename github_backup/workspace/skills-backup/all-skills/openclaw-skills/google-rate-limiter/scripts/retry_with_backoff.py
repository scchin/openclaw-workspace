#!/usr/bin/env python3
"""
Google Model API Retry Script with Exponential Backoff

Usage:
    python3 retry_with_backoff.py --model "gemma-4-31b-it" --prompt "Hello"
    python3 retry_with_backoff.py --model "gemma-4-31b-it" --prompt "Explain AI" --max-retries 5 --initial-delay 10
"""

import argparse
import os
import time
import json
import ssl
import urllib.request
import urllib.error

# Mac SSL fix: use bundled certs
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CONTEXT = ssl._create_unverified_context()


def call_google_model(model: str, prompt: str, api_key: str = None, max_tokens: int = 100) -> dict:
    """Call Google Gemini API directly via urllib (no external dependencies)."""

    if api_key is None:
        api_key = os.environ.get("GOOGLE_API_KEY", "")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

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
    """Check if the result indicates a 429 rate limit error."""
    if not result.get("success") and result.get("status_code") == 429:
        return True

    error = result.get("error", {})
    if isinstance(error, dict):
        status = error.get("status", "")
        code = error.get("code", 0)
        message = error.get("message", "")

        if status in ("RESOURCE_EXHAUSTED", "rateLimitExceeded") or \
           code == 429 or \
           "exhausted" in message.lower() or \
           "rate limit" in message.lower():
            return True

    return False


def format_response(result: dict) -> str:
    """Extract the text response from a successful API call."""
    try:
        candidates = result.get("data", {}).get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part and part.get("thought") is not True:
                    return part["text"]
            # If all parts are thoughts, return the last one
            if parts:
                return parts[-1].get("text", "[no text]")
        return "[no response]"
    except Exception:
        return "[parse error]"


def main():
    parser = argparse.ArgumentParser(description="Retry Google model calls with exponential backoff")
    parser.add_argument("--model", default="gemma-4-31b-it", help="Model ID (default: gemma-4-31b-it)")
    parser.add_argument("--prompt", required=True, help="Prompt text")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retry attempts (default: 3)")
    parser.add_argument("--initial-delay", type=float, default=10.0, help="Initial delay seconds (default: 10)")
    parser.add_argument("--max-delay", type=float, default=60.0, help="Max delay seconds (default: 60)")
    parser.add_argument("--api-key", help="Google API Key (or set GOOGLE_API_KEY env)")
    parser.add_argument("--max-tokens", type=int, default=100, help="Max output tokens (default: 100)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    delay = args.initial_delay
    last_error_msg = ""

    for attempt in range(1, args.max_retries + 1):
        print(f"\nAttempt {attempt}/{args.max_retries}: Calling {args.model}...")

        result = call_google_model(args.model, args.prompt, args.api_key, args.max_tokens)

        if result.get("success"):
            response_text = format_response(result)
            print(f"✅ Success! Response: {response_text}")

            if args.verbose:
                usage = result.get("data", {}).get("usageMetadata", {})
                print(f"   Tokens: prompt={usage.get('promptTokenCount')}, output={usage.get('candidatesTokenCount')}")

            return 0
        else:
            last_error_msg = result.get("error", {}).get("message", str(result.get("error")))

            if is_rate_limit_error(result):
                if attempt < args.max_retries:
                    wait = min(delay, args.max_delay)
                    print(f"⚠️  Rate limit hit (429). Waiting {wait:.0f} seconds before retry...")
                    print(f"   Error: {last_error_msg[:100]}")
                    time.sleep(wait)
                    delay *= 2  # Exponential backoff
                else:
                    print(f"❌ Failed after {args.max_retries} attempts (rate limited)")
                    print(f"   Last error: {last_error_msg}")
                    return 1
            else:
                print(f"❌ Non-retryable error: {last_error_msg}")
                return 1

    return 0


if __name__ == "__main__":
    exit(main())
