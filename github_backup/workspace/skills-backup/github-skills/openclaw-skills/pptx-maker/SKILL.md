---
name: pptx-maker
description: 使用 python-pptx 建立、編輯 PowerPoint 簡報（.pptx）。當用戶需要建立簡報、加入文字、圖片、圖表、或修改版面時使用此技能。
---

# PPTX Maker

使用 `python-pptx` + `/usr/local/bin/python3` 建立與編輯 PowerPoint 簡報。

## 使用方式

### 1. 基本操作（用 python 脚本）

所有操作透過 `uv run` 或直接用 `/usr/local/bin/python3` 執行 `python-pptx`。

### 2. 建立新簡報

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# 加入標題頁
blank_layout = prs.slide_layouts[6]  # 空白版面
slide = prs.slides.add_slide(blank_layout)
title = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11), Inches(2))
tf = title.text_frame
p = tf.paragraphs[0]
p.text = "簡報標題"
p.font.size = Pt(54)
p.font.bold = True

prs.save("/Users/KS/output.pptx")
```

### 3. 加入內容頁

```python
slide = prs.slides.add_slide(blank_layout)
content = slide.shapes.add_textbox(Inches(0.5), Inches(1), Inches(12), Inches(5))
tf = content.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "第一段文字"
p.font.size = Pt(24)
p.space_after = Pt(12)
```

### 4. 加入圖片

```python
slide.shapes.add_picture("/path/to/image.png", Inches(1), Inches(1), width=Inches(4))

### 5. 常用工具函式

執行路徑：`/usr/local/bin/python3`

版面參考：
- `prs.slide_layouts[0]` = 標題頁
- `prs.slide_layouts[1]` = 標題 + 內容
- `prs.slide_layouts[6]` = 空白

顏色：`RGBColor(0xFF, 0x00, 0x00)` = 紅色
字體大小：`Pt(12)` ~ `Pt(72)`

### 限制
- 圖表（Chart）需要額外依賴，優先用形狀（shape）代替
- 動畫不支援（python-pptx 唯讀）
