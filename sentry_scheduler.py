#!/usr/bin/env python3
import sys
from datetime import datetime, timedelta, timezone

def get_future_utc_time(delay_seconds):
    """計算從現在起延遲 N 秒後的 ISO-8601 UTC 時間戳"""
    # 獲取精確的 UTC 現在時間
    now_utc = datetime.now(timezone.utc)
    # 加上延遲
    future_utc = now_utc + timedelta(seconds=delay_seconds)
    # 格式化為 ISO-8601 (Z 表示 UTC)
    return future_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 sentry_scheduler.py <delay_seconds>")
        sys.exit(1)
    
    try:
        delay = int(sys.argv[1])
        print(get_future_utc_time(delay))
    except ValueError:
        print("Error: Delay must be an integer (seconds).")
        sys.exit(1)

if __name__ == "__main__":
    main()
