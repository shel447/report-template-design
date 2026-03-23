#!/usr/bin/env python3
"""生成大纲即蓝图验证（Blueprint Compiler）原理 PPT"""
from pptx import Presentation
from pptx.util import Pt, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ── 色彩定义
HW_RED    = RGBColor(0xC7, 0x00, 0x0F)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
DARK_BG   = RGBColor(0x2E, 0x2E, 0x2E)
ALT_BG    = RGBColor(0xF0, 0xF0, 0xF0)
LIGHT_RED = RGBColor(0xFF, 0xE5, 0xE5)
FONT_CN   = "微软雅黑"
FONT_MONO = "Consolas"

prs = Presentation()
prs.slide_width  = Cm(33.87)
prs.slide_height = Cm(19.05)
slide = prs.slides.add_slide(prs.slide_layouts[6])

def add_rect(l, t, w, h, fill_color, line_color=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(l), Cm(t), Cm(w), Cm(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill_color
    if line_color:
        s.line.color.rgb = line_color
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    return s

def add_text(l, t, w, h, text, size, color=DARK_BG, bold=False, align=PP_ALIGN.LEFT, font=FONT_CN):
    box = slide.shapes.add_textbox(Cm(l), Cm(t), Cm(w), Cm(h))
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = str(text)
    r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color; r.font.name = font
    return box

def add_arrow(l, t, w, h):
    s = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Cm(l), Cm(t), Cm(w), Cm(h))
    s.fill.solid(); s.fill.fore_color.rgb = HW_RED
    s.line.fill.background()

# ── 标题与修饰 ──
add_rect(0,       0, 33.87, 2.0, HW_RED)
add_rect(0,   18.65, 33.87, 0.4, HW_RED)
add_text(1.0, 0.2, 30, 1.0, "报告大纲架构重塑：基于 Notion 蓝图的单向编译器模式", 20, color=WHITE, bold=True)
add_text(1.0, 1.2, 30, 0.8, "大纲（Outline）不再是生成结果厚的快照，而是严谨的意图区块集合，作为向底层执行层编译的源头指令", 10, color=WHITE)

# ==========================================
# 左侧：蓝图层 (前端交互视角)
# ==========================================
add_text(1.0,   2.5, 12.0, 0.5, "第一层：大纲蓝图层 (YAML `outline`)", 14, color=HW_RED, bold=True, align=PP_ALIGN.CENTER)
add_text(1.0,   3.2, 12.0, 0.8, "UI 所见即所得编辑。不含任何数据库真实数据，纯粹由指令意图构成的大纲结构（Blueprint）。", 8.5, color=DARK_BG)
add_rect(1.0,   4.3, 12.0, 14.0, ALT_BG)

tree1 = """outline:
  - id: "blk_intro"
    type: "paragraph"
    content: "当前设备主轴承的..."
    
  # [UI 强制组件: 填入一个数值]
  - id: "blk_metric_vib"
    type: "metric"
    intent: "查询设备当前最近一次..."
    
  # [UI 强制组件: AI 测评]
  - id: "blk_ai_diag"
    type: "ai_summary"
    intent: "评估是否存在风险,伴随轻微漏油"
    
  # [UI 强制组件: 一个图表壳子]
  - id: "blk_chart_trend"
    type: "chart"
    intent: "近 3 天的振动趋势折线图" """

add_text(1.2, 4.4, 11.6, 13.5, tree1, 9, font=FONT_MONO)


# ==========================================
# 中间：编译层 (Agent Copilot)
# ==========================================
add_text(14.0, 8.5, 4.0, 0.8, "Agent (Template Copilot)\n降维翻译与架构生成\n（保存时刻发生）", 10, color=HW_RED, bold=True, align=PP_ALIGN.CENTER)
add_arrow(14.5, 9.5, 3.0, 0.6)


# ==========================================
# 右侧：运行层 (底层 YAML 骨架)
# ==========================================
add_text(19.0,   2.5, 13.0, 0.5, "第二层：底层骨架层 (YAML `content`)", 14, color=HW_RED, bold=True, align=PP_ALIGN.CENTER)
add_text(19.0,   3.2, 13.0, 0.8, "编译成果（AST）。结构极为严谨，Data Engine 将以此为据，连接数据库跑批产生 8.5mm/s 这样的结果。", 8.5, color=DARK_BG)
add_rect(19.0,   4.3, 13.0, 14.0, ALT_BG)

tree2 = """content:
  datasets:
    # 响应 blk_metric_vib 意图
    - id: "ds_metric_vib"
      source: { kind: nl2sql, desc: "查最近一次振幅" }
      
    # 响应 blk_chart_trend 意图
    - id: "ds_trend_chart"
      source: { kind: nl2sql, desc: "查近3天振幅" }
      
    # 响应 blk_ai_diag 意图
    - id: "ds_synthesis" ...
      source: { kind: ai_synthesis, prompt: "轻微漏油" }
      
  presentation:
    type: composite_table
    sections:
      - band: "振动诊断结论"
        layout: { type: mixed_text, dataset_id: "ds_synthesis" }
        
      # 响应 blk_chart_trend 配备的 UI 壳子
      - band: "辅助分析趋势图"
        layout: { type: chart, chart_type: "line", dataset_id: "ds_trend_chart" } """

# 高亮背景框（展示映射关系）
add_rect(19.2,   5.7, 12.6, 1.2, LIGHT_RED)
add_rect(19.2,   7.5, 12.6, 1.2, LIGHT_RED)
add_rect(19.2,   9.3, 12.6, 1.2, LIGHT_RED)
add_rect(19.2,  15.2, 12.6, 1.5, LIGHT_RED)

add_text(19.2, 4.4, 12.6, 13.5, tree2, 9, font=FONT_MONO)


# 保存
out = r"e:\code\antigravity_projects\ReportTemplate\output\outline_compiler.pptx"
prs.save(out)
print(f"Saved: {out}")
