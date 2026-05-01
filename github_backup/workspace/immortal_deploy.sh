#!/bin/bash

# ==============================================================================
# 🗝️ Immortal Deployer (不朽發布鑰匙)
# 版本: v1.0
# 描述: 負責將 Workspace 的技能以 100% 物理精準度發布至 DNA 金庫與全域發布區。
# ==============================================================================

set -e

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}   🗝️ OpenClaw Immortal Deployer 啟動   ${NC}"
echo -e "${BLUE}==========================================${NC}"

if [ "$#" -ne 2 ]; then
    echo -e "${RED}❌ 語法錯誤！${NC}"
    echo -e "使用方式: $0 <技能名稱> <版本號>"
    echo -e "範例: $0 openclaw-soul-sync 1.0.0"
    exit 1
fi

SKILL_NAME=$1
VERSION=$2

WORKSPACE_DIR="$HOME/.openclaw/workspace/skills/$SKILL_NAME"
DNA_DIR="$HOME/.openclaw/dna/skills/$SKILL_NAME"
RELEASE_DIR="$HOME/.agents/skills/$SKILL_NAME-$VERSION"

if [ ! -d "$WORKSPACE_DIR" ]; then
    echo -e "${RED}❌ 錯誤: 找不到工作區目錄 ${WORKSPACE_DIR}${NC}"
    exit 1
fi

echo -e "\n${YELLOW}▶ 第一階段：解除實體武裝 (nouchg)...${NC}"
chflags -R nouchg "$WORKSPACE_DIR" 2>/dev/null || true
chflags -R nouchg "$DNA_DIR" 2>/dev/null || true
chflags -R nouchg "$RELEASE_DIR" 2>/dev/null || true
echo -e "${GREEN}✅ 解除完畢。${NC}"

echo -e "\n${YELLOW}▶ 第二階段：DNA 基因同化 (Workspace -> DNA Vault)...${NC}"
mkdir -p "$DNA_DIR"
# 使用 rsync 確保完全鏡像同步，刪除多餘檔案
rsync -av --delete --exclude '__pycache__' --exclude '*.pyc' "$WORKSPACE_DIR/" "$DNA_DIR/" > /dev/null
echo -e "${GREEN}✅ DNA 金庫更新完畢。${NC}"

echo -e "\n${YELLOW}▶ 第三階段：全域發布 (DNA Vault -> Global Registry)...${NC}"
mkdir -p "$RELEASE_DIR"
rsync -av --delete --exclude '__pycache__' --exclude '*.pyc' "$DNA_DIR/" "$RELEASE_DIR/" > /dev/null
echo -e "${GREEN}✅ 官方發布區更新完畢 (版本: $VERSION)。${NC}"

echo -e "\n${YELLOW}▶ 第四階段：終極實體鎖定 (uchg)...${NC}"
# 只針對核心邏輯 (.py) 與說明文檔 (.md) 進行實體鎖定
find "$WORKSPACE_DIR" -type f \( -name "*.py" -o -name "*.md" \) -exec chflags uchg {} +
find "$DNA_DIR" -type f \( -name "*.py" -o -name "*.md" \) -exec chflags uchg {} +
find "$RELEASE_DIR" -type f \( -name "*.py" -o -name "*.md" \) -exec chflags uchg {} +
echo -e "${GREEN}✅ 物理防禦裝甲 (uchg) 啟動完畢。${NC}"

echo -e "\n${BLUE}==========================================${NC}"
echo -e "${GREEN}🏆 部署成功！${NC}"
echo -e "技能: ${SKILL_NAME}"
echo -e "狀態: 100% 基因一致，防禦系統已鎖定。"
echo -e "${BLUE}==========================================${NC}"
