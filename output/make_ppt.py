#!/usr/bin/env python3
"""生成报告模板结构 PPT（华为红色风格）"""
from pptx import Presentation
from pptx.util import Pt, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── 色彩定义
HW_RED    = RGBColor(0xC7, 0x00, 0x0F)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
DARK      = RGBColor(0x1F, 0x1F, 0x1F)
ALT       = RGBColor(0xF5, 0xF5, 0xF5)
LT_RED    = RGBColor(0xFF, 0xCC, 0xCC)
FONT_CN   = "微软雅黑"

prs = Presentation()
prs.slide_width  = Cm(33.87)
prs.slide_height = Cm(19.05)
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

# ── 白色背景
def rect(l, t, w, h, fill, line=False):
    s = slide.shapes.add_shape(1, Cm(l), Cm(t), Cm(w), Cm(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if not line: s.line.fill.background()
    return s

rect(0, 0, 33.87, 19.05, WHITE)

# ── 顶部红色横幅
rect(0, 0, 33.87, 2.4, HW_RED)

# ── 底部红色横条
rect(0, 18.55, 33.87, 0.5, HW_RED)

# ── 左侧竖线分隔（装饰）
rect(16.65, 2.5, 0.06, 15.9, RGBColor(0xDD, 0xDD, 0xDD))

# ── 文本框辅助
def tb(text, l, t, w, h, size, bold=False, color=DARK,
       align=PP_ALIGN.LEFT, wrap=False):
    box = slide.shapes.add_textbox(Cm(l), Cm(t), Cm(w), Cm(h))
    tf = box.text_frame; tf.word_wrap = wrap
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color; r.font.name = FONT_CN
    return box

# 标题
tb("智能报告模板系统  ·  数据结构定义",
   1.0, 0.2, 30, 1.3, 20, bold=True, color=WHITE)
tb("Template Root  |  Parameter  |  Section  |  Content Source  |  Presentation  |  Composite Table Layout",
   1.0, 1.6, 32, 0.65, 7.5, color=LT_RED)
tb("© Report Template System v1.0  |  2026-03",
   1.0, 18.55, 20, 0.48, 7, color=WHITE)

# ── 区段标签辅助
def label(text, l, t, w=15.0):
    rect(l, t+0.09, 0.18, 0.44, HW_RED)          # 红色竖条
    tb(text, l+0.28, t, w, 0.58, 8.5, bold=True, color=HW_RED)

# ── 表格辅助
def table(data, l, t, w, h, col_fracs, fs=7.5, hdr=1):
    rows, cols = len(data), len(data[0])
    shp = slide.shapes.add_table(rows, cols, Cm(l), Cm(t), Cm(w), Cm(h))
    tbl = shp.table
    for i, f in enumerate(col_fracs):
        tbl.columns[i].width = Cm(w * f)
    for ri, row in enumerate(data):
        is_h = ri < hdr
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.margin_left = Cm(0.1); cell.margin_right = Cm(0.06)
            cell.margin_top = Cm(0.04); cell.margin_bottom = Cm(0.04)
            tf = cell.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run(); r.text = str(val)
            r.font.size = Pt(fs); r.font.name = FONT_CN
            r.font.bold = is_h
            if is_h:
                r.font.color.rgb = WHITE
                cell.fill.solid(); cell.fill.fore_color.rgb = HW_RED
            else:
                r.font.color.rgb = DARK
                cell.fill.solid()
                cell.fill.fore_color.rgb = ALT if ri % 2 == 0 else WHITE
    return shp

# ════════════════════════════════════════════════════
# 左列  x: 0.5 ~ 16.4
# ════════════════════════════════════════════════════
LW = 15.7   # 左列宽

# ── TABLE 1: 模板根字段
label("模板根字段（Template Root）", 0.5, 2.52)
table([
    ["字段",          "类型",   "说明"],
    ["id",            "string", "模板唯一标识（a-z / 0-9 / _）"],
    ["type",          "string", "报告类型（如：设备健康评估）"],
    ["scene",         "string", "场景细分（如：总部）"],
    ["name",          "string", "模板展示名称"],
    ["parameters[]",  "array",  "参数定义列表（详见「参数」表）"],
    ["sections[]",    "array",  "报告章节树（可多级嵌套，详见「章节」表）"],
], 0.5, 3.12, LW, 3.85, [0.16, 0.09, 0.75])

# ── TABLE 3: 章节结构
label("章节结构（sections[] 字段）", 0.5, 7.22)
table([
    ["字段",           "说明"],
    ["id",             "区段标识，供 ai_synthesis refs 引用"],
    ["title",          "章节标题，支持 {param} / {$var} 占位符"],
    ["band",           "可选，区段标题行（自动全宽 colspan）"],
    ["foreach.param",  "绑定的多值参数 id（需 multi:true），按每值展开章节"],
    ["foreach.as",     "迭代变量名，内容中以 {$as} 引用"],
    ["content",        "叶节点内容（与 subsections 互斥）"],
    ["subsections[]",  "子章节列表（与 content 互斥）"],
], 0.5, 7.82, LW, 4.3, [0.24, 0.76])

# ════════════════════════════════════════════════════
# 右列  x: 17.0 ~ 33.5
# ════════════════════════════════════════════════════
RX = 17.0
RW = 16.3

# ── TABLE 2: 参数定义
label("参数定义（parameters[] 字段）", RX, 2.52, RW)
table([
    ["字段",       "必填", "说明"],
    ["id",         "✓",   "参数唯一标识，内容中以 {id} 引用"],
    ["label",      "✓",   "用户可读名称（用于对话提示）"],
    ["required",   "✓",   "布尔值，是否必填"],
    ["input_type", "✓",   "free_text（自由输入）/ enum（枚举）/ dynamic（动态选项）"],
    ["multi",      "—",   "true 时允许多值，可作为 foreach 的绑定来源"],
    ["options",    "条件", "input_type=enum 时的枚举选项列表"],
    ["source",     "条件", "input_type=dynamic 时的动态来源（接口 URL 或 SQL）"],
], RX, 3.12, RW, 4.45, [0.14, 0.07, 0.79])

# ── TABLE 4: 数据来源
label("数据来源（source.kind）", RX, 7.82, RW)
table([
    ["kind",          "关键字段",                      "说明"],
    ["sql",           "query",                         "直接执行参数化 SQL，支持 {param} / {$var} 占位符"],
    ["nl2sql",        "description",                   "自然语言描述 → LLM 生成 SQL → 执行"],
    ["ai_synthesis",  "context / knowledge / prompt",  "多源上下文（refs+queries）+ RAG 知识检索 + LLM 合成"],
], RX, 8.42, RW, 2.25, [0.16, 0.24, 0.60])

# ── TABLE 5: 呈现形式
label("呈现形式（presentation.type）", RX, 10.92, RW)
table([
    ["type",            "关键字段",           "支持 source.kind",   "说明"],
    ["text",            "template",           "（无）",              "静态文本 + 占位符替换"],
    ["value",           "anchor",             "sql",                 "SQL 单值嵌入锚点文本 {$value}"],
    ["chart",           "chart_type",         "sql / nl2sql",        "可视化图形（bar / line / pie …）"],
    ["simple_table",    "—",                 "sql / nl2sql",        "普通二维明细表格"],
    ["composite_table", "columns, sections[]","sql / ai_synthesis",  "复合合并表格（见下方）"],
], RX, 11.52, RW, 3.2, [0.18, 0.17, 0.19, 0.46])

# ════════════════════════════════════════════════════
# 全宽底部  TABLE 6: 复合表格分区布局
# ════════════════════════════════════════════════════
label("复合表格分区布局（composite_table  sections[]  layout）", 0.5, 15.1, 33.0)
table([
    ["layout.type", "结构字段",                                    "约束规则",                                                  "数据填充方式"],
    ["kv_grid",     "cols_per_row · key_span · value_span · fields[]",
                    "(key_span + value_span) × cols_per_row = columns；fields 不足末行以空白补齐",
                    "fields[].value（参数直填）/ fields[].col（SQL 单行按列名）/ key_col + value_col（SQL 动态 KV 展开）"],
    ["tabular",     "headers[] · columns[]",
                    "headers[].span 之和 = columns",
                    "columns[].field（SQL / nl2sql 多行结果）/ ~dynamic~ 标记（PIVOT 动态列，列数运行时确定）"],
], 0.5, 15.7, 33.0, 2.6, [0.08, 0.19, 0.28, 0.45])

# 保存
out = r"e:\code\antigravity_projects\ReportTemplate\output\report_template_structure.pptx"
prs.save(out)
print(f"Saved: {out}")
