#!/bin/bash
#===========================================================
# 中國日期查詢工具 - 安裝腳本
# 在新電腦上執行此腳本即可完成所有設定
#===========================================================

set -e

echo "=================================================="
echo "  🌏 中國日期查詢工具 - 安裝腳本"
echo "=================================================="

# 顏色
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

ok()  { echo -e "  ${GREEN}✔${NC} $1"; }
warn(){ echo -e "  ${YELLOW}⚠${NC} $1"; }
fail(){ echo -e "  ${RED}✖${NC} $1"; }

#----------------------------------------------------------
# 1. 檢查 Node.js
#----------------------------------------------------------
echo ""
echo "▶ 檢查環境..."

if ! command -v node &>/dev/null; then
    fail "Node.js 未安裝（請先安裝 Node.js）"
    exit 1
fi
ok "Node.js: $(node --version)"

#----------------------------------------------------------
# 2. 安裝 cantian-tymext
#----------------------------------------------------------
echo ""
echo "▶ 安裝 cantian-tymext（命理引擎）..."

if npm list -g cantian-tymext &>/dev/null; then
    ok "cantian-tymext 已安裝"
else
    npm install -g cantian-tymext 2>&1 | tail -3
    ok "cantian-tymext 安裝完成"
fi

#----------------------------------------------------------
# 3. 安裝 Python（若需要）
#----------------------------------------------------------
echo ""
echo "▶ 檢查 Python..."

PYTHON_BIN=""
for bin in /usr/local/bin/python3 /opt/homebrew/bin/python3 /usr/bin/python3; do
    if [ -f "$bin" ]; then
        PYTHON_BIN="$bin"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    warn "Python3 未找到（某些功能可能受限）"
else
    ok "Python: $($PYTHON_BIN --version 2>&1 | head -1)"

    # 安裝 lunarcalendar
    echo ""
    echo "▶ 安裝 lunarcalendar（Python 農曆庫）..."
    $PYTHON_BIN -m pip install lunarcalendar --break-system-packages -q 2>&1 | tail -3
    ok "lunarcalendar 安裝完成"
fi

#----------------------------------------------------------
# 4. 找出 cantian-tymext 的 node_modules 路徑
#----------------------------------------------------------
echo ""
echo "▶ 設定路徑..."

NODE_MODULES=$(npm root -g)
ok "全域 node_modules: $NODE_MODULES"

#----------------------------------------------------------
# 5. 驗證
#----------------------------------------------------------
echo ""
echo "▶ 驗證安裝..."

TEST_OUT=$(node -e "
const { createRequire } = require('module');
const req = createRequire('$NODE_MODULES/');
const { buildBaziFromSolar } = req('cantian-tymext');
const bazi = buildBaziFromSolar({ solarTime: '2026-03-20 00:54:58' });
const parts = bazi.八字.split(' ');
console.log(JSON.stringify({year: parts[0], month: parts[1], day: parts[2], hour: parts[3], zodiac: bazi.生肖}));
" 2>&1)

if echo "$TEST_OUT" | grep -q "丙午"; then
    ok "命理引擎驗證成功：$TEST_OUT"
else
    warn "命理引擎驗證輸出：$TEST_OUT"
fi

#----------------------------------------------------------
# 6. 測試主程式
#----------------------------------------------------------
echo ""
echo "▶ 測試主程式..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/date_query.py" ]; then
    if [ -n "$PYTHON_BIN" ]; then
        RESULT=$($PYTHON_BIN "$SCRIPT_DIR/date_query.py" 2>&1)
        if echo "$RESULT" | grep -q "干支"; then
            ok "主程式測試成功"
        else
            warn "主程式輸出：$RESULT"
        fi
    else
        warn "跳過主程式測試（Python 未安裝）"
    fi
fi

#----------------------------------------------------------
# 完成
#----------------------------------------------------------
echo ""
echo "=================================================="
echo -e "  ${GREEN}✔ 安裝完成！${NC}"
echo "=================================================="
echo ""
echo "使用方式："
echo "  /usr/local/bin/python3 $SCRIPT_DIR/date_query.py        # 查詢今天"
echo "  /usr/local/bin/python3 $SCRIPT_DIR/date_query.py 2026 3 20 0 54  # 查指定時間"
echo ""
echo "若路徑不同，請調整 PYTHON_BIN 和 NODE_MODULES_DIR"
echo ""
