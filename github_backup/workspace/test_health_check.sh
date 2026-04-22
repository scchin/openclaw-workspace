#!/bin/zsh

# Test script for system_health_check.py

SCRIPT="/Users/KS/.openclaw/workspace/system_health_check.py"

echo "=== Testing LIGHT Intensity ==="
python3 "$SCRIPT" --intensity LIGHT
echo "\n"

echo "=== Testing STANDARD Intensity ==="
python3 "$SCRIPT" --intensity STANDARD
echo "\n"

echo "=== Testing STRICT Intensity ==="
python3 "$SCRIPT" --intensity STRICT
echo "\n"
