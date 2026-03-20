#!/usr/bin/env python3
"""生成大纲交互运行时流程图 PPT（华为红色风格）"""
from pptx import Presentation
from pptx.util import Pt, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ── 色彩定义
HW_RED    = RGBColor(0xC7, 0x00, 0x0F)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
DARK_BG   = RGBColor(0x33, 0x33, 0x33)
ALT_BG    = RGBColor(0xF9, 0xF9, 0xF9)
LT_RED    = RGBColor(0xFF, 0xEB, 0xEB)
HW_GREY   = RGBColor(0x77, 0x77, 0x77)
FONT_CN   = "微软雅黑"

prs = Presentation()
prs.slide_width  = Cm(33.87)
prs.slide_height = Cm(19.05)
slide = prs.slides.add_slide(prs.slide_layouts[6])

def add_rect(l, t, w, h, fill_color, line_color=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(l), Cm(t), Cm(w), Cm(h))
    s.fill.solid()
    if fill_color:
        s.fill.fore_color.rgb = fill_color
    else:
        s.fill.background()
    if line_color:
        s.line.color.rgb = line_color
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    return s

def add_arrow(l, t, w, h):
    s = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Cm(l), Cm(t), Cm(w), Cm(h))
    s.fill.solid(); s.fill.fore_color.rgb = HW_GREY
    s.line.fill.background()

def add_text(l, t, w, h, text, size, color=DARK_BG, bold=False, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(Cm(l), Cm(t), Cm(w), Cm(h))
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = str(text)
    r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color; r.font.name = FONT_CN
    return box

# ── 标题与修饰 ──
add_rect(0, 0, 33.87, 2.4, HW_RED)
add_rect(0, 18.55, 33.87, 0.5, HW_RED)
add_text(1.0, 0.3, 30, 1.3, "报告生成运行时：大纲交与意图融合(WYSIWYG)流程", 22, color=WHITE, bold=True)
add_text(1.0, 1.45, 30, 0.8, "展示用户意图修改如何影响最终生成，以及对“越界意图”的柔性处理机制", 10, color=WHITE)

# ==========================================
# 绘制四大核心阶段
# ==========================================

configs = [
    {
        "y": 3.5,
        "step": "Phase 1: 模板解析与取数",
        "action": "引擎加载 parameters，按 DAG 调度并执行无依赖的 datasets，从数据库查询出客观数值状态。",
        "template_use": "读取 datasets[].source.query\n执行 SQL / 调用 API",
        "output": "【客观事实数据集】\n例如：设备各测点当前温度 92℃，处于超标状态。",
        "color": ALT_BG
    },
    {
        "y": 7.0,
        "step": "Phase 2: 大纲初稿生成 (Draft)",
        "action": "利用查出的事实数据，注入大纲层预设的大纲指令，让 LLM 快速生成每个章节的“剧情摘要”。",
        "template_use": "读取 outline.draft_prompt\n结合 parameters + 客观事实",
        "output": "【大纲预览文本】\n例如：“发现设备测点超温现象，本章将讨论轴承磨损的可能性。”",
        "color": WHITE
    },
    {
        "y": 10.5,
        "step": "Phase 3: 用户界面交互 (WYSIWYG)",
        "action": "用户在界面看到大纲进行修改。若用户补充了数据库查不到的观察（如“现场闻到焦味”），即发生“意图越界”。",
        "template_use": "受控于 presentation.user_editable 标志\n系统绑定修改至 {$user_note} 变量",
        "output": "【强意图变量/上下文】\n用户的补充文字、对主旨的修改，被作为新的 Context 保存。",
        "color": LT_RED
    },
    {
        "y": 14.0,
        "step": "Phase 4: 最终报告编织 (AI Synthesis)",
        "action": "不再僵硬使用 SQL，而是将【客观事实】+【用户强意图】共同注入 ai_synthesis。AI 将用户补充的越界信息作为“现场人工观察”融入专业诊断，不引发逻辑断裂。",
        "template_use": "执行依赖尾部的 datasets (kind: ai_synthesis)\nprompt_template 包含 {$user_note}",
        "output": "【最终正式报告段落】\n“结合系统记录的超温事实与现场排查反馈的金属性异味，判定为...”",
        "color": ALT_BG
    }
]

for i, cfg in enumerate(configs):
    y = cfg["y"]
    # 绘制背景条块
    add_rect(1.0, y, 31.87, 2.5, cfg["color"], line_color=RGBColor(210,210,210))
    
    # 左侧：阶段名
    add_rect(1.0, y, 6.0, 2.5, HW_RED)
    add_text(1.2, y + 0.9, 5.6, 1.0, cfg["step"], 12, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    
    # 分割线 1
    add_rect(14.0, y, 0.05, 2.5, RGBColor(220,220,220))
    # 分割线 2
    add_rect(23.0, y, 0.05, 2.5, RGBColor(220,220,220))
    
    # 栏目 1：引擎动作
    add_text(7.5, y + 0.2, 5.0, 0.5, "▶ 引擎核心动作", 11, color=HW_RED, bold=True)
    add_text(7.5, y + 0.9, 6.0, 1.5, cfg["action"], 9, color=DARK_BG)
    
    # 栏目 2：模板触点
    add_text(14.5, y + 0.2, 5.0, 0.5, "▶ 模板信息运用 (Template)", 11, color=HW_RED, bold=True)
    add_text(14.5, y + 0.9, 8.0, 1.5, cfg["template_use"], 9, color=DARK_BG, bold=True)
    
    # 栏目 3：阶段产出 & 越界影响
    add_text(23.5, y + 0.2, 5.0, 0.5, "▶ 阶段产出与对终稿的影响", 11, color=HW_RED, bold=True)
    add_text(23.5, y + 0.9, 9.0, 1.5, cfg["output"], 9, color=DARK_BG)
    
    # 绘制向下的箭头 (除了最后一个)
    if i < len(configs) - 1:
        add_arrow(16.5, y + 2.6, 0.6, 0.8)

# 保存
out = r"e:\code\antigravity_projects\ReportTemplate\output\outline_workflow.pptx"
prs.save(out)
print(f"Saved: {out}")
