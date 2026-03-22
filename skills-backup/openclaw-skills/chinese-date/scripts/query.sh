#!/bin/bash
# 便捷 wrapper：直接用 bash date_query.sh [年 月 日 時 分]
# 會自動找到系統上的 Python3 並執行

DIR="$(cd "$(dirname "$0")" && pwd)"

# 自動找 Python3
PYTHON_BIN=""
for bin in /usr/local/bin/python3 /opt/homebrew/bin/python3 /usr/bin/python3; do
    if [ -f "$bin" ]; then
        PYTHON_BIN="$bin"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "錯誤：找不到 Python3"
    exit 1
fi

exec "$PYTHON_BIN" "$DIR/date_query.py" "$@"
