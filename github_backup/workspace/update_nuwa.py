import sys

file_path = '/Users/KS/.openclaw/workspace/.agents/skills/huashu-nuwa/SKILL.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Modification 1: Path replacement
content = content.replace('.claude/skills/[person-name]-perspective/', '/Users/KS/.openclaw/workspace/.agents/skills/huashu-nuwa/examples/[person-name]-perspective/')

# Modification 2: Register step
# Find the line "#### Step 4: 输出" and append the registration section after the write command.
old_step4 = '#### Step 4: 输出\n将完成的SKILL.md写入 `.claude/skills/[person-name]-perspective/SKILL.md`。'
# Note: since I already replaced the path in 'content', the text to search for is different.
# Let's do it carefully.

# The original line was "将完成的SKILL.md写入 `.claude/skills/[person-name]-perspective/SKILL.md`。"
# Now it is "将完成的SKILL.md写入 `/Users/KS/.openclaw/workspace/.agents/skills/huashu-nuwa/examples/[person-name]-perspective/SKILL.md`。"

target_line = '将完成的SKILL.md写入 `/Users/KS/.openclaw/workspace/.agents/skills/huashu-nuwa/examples/[person-name]-perspective/SKILL.md`。'
registration_section = '\n\n### Phase 3.5: 專家登記 (Expert Registration)\n\n**這是確保專家能被 DED (虛擬專家工作小組) 辨識的關鍵步驟。**\n\n在完成 Skill 構建後，必須立即執行以下登記操作：\n1. **提取 DNA**：從 Phase 2 的提煉結果中，提取「專家名稱」、「核心專長」、「認知原型」與「邏輯模式」。\n2. **格式對齊**：參考 `/Users/KS/.openclaw/workspace/EXPERT_REGISTRY.md` 的表格格式。\n3. **寫入登記**：將該專家的 DNA 條目追加寫入至 `EXPERT_REGISTRY.md` 的表格末尾。\n4. **驗證**：確認寫入後，該專家應能立即被 `nuwa-dispatcher` 匹配。'

if target_line in content:
    content = content.replace(target_line, target_line + registration_section)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modification successful.")
