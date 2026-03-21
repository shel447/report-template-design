# 大纲交互（WYSIWYG）三态演化全过程解析

为了清晰展示所见即所得大纲（Outline）机制如何在保证数据客观性的前提下实现极高的灵活性，我们将通过一个报告节点的“生命周期”，展示其底层 JSON/YAML 结构在**三个阶段**的变化。

---

## 阶段一：纯模板态 (Pure Template)
**场景**：技术人员在后台配置完成的静态模板。尚未填充任何真实跑批数据，也未在前端展现给最终用户查看。

**结构特征**：
- `outline` 仅有 `draft_prompt`（指导方针），没有任何实际运行产生的文本。
- `datasets` 和 `presentation` 只包含该模板最初设计的、最基础的数据展现块（例如只有一个静态 SQL）。

```yaml
title: "3.2 主轴承运行状态分析"
outline:
  draft_prompt: "提取 ds_vibration 的结论，用一句话概括主轴承状态"
  # 这里没有任何运行时态！

content:
  datasets:
    # 唯一的数据池，固定查询振动信息
    - id: "ds_vibration"
      source:
        kind: sql
        query: "SELECT val, limit FROM vibration_logs WHERE device_id = '{$device}'"
        
    - id: "ds_synthesis"
      depends_on: ["ds_vibration"]
      source:
        kind: ai_synthesis
        context:
          refs: ["ds_vibration"]
        knowledge:
          query_template: "针对轴承振动寻找关联故障指南"
          params: 
            subject: "主轴承"
            symptoms: "refs.ds_vibration[status_tag='异常']"
        prompt: "请依据测点数据评估故障。"

  presentation:
    type: composite_table
    columns: 8
    sections:
      - band: "振动诊断结论"
        layout:
          type: kv_grid
          dataset_id: "ds_synthesis"
          # ...
```

---

## 阶段二：赋值后未修改的草稿态 (Draft Generated)
**场景**：系统开始为该设备填报数据。后端提取出了客观的 SQL 事实，并拿着事实及 `draft_prompt` 去请求了 LLM，生出了一段初版摘要，发送到正在预览草稿 Web 页面的客户端上。

**结构特征**：
- `outline` 中多出了引擎回填的 `original_draft`，作为原始草稿的留档。用户在界面上看到的文本输入框，内容就是这段字。
- `content` 部分与“阶段一”完・全・一・致，客观数据未被任何扭曲。

```yaml
title: "3.2 主轴承运行状态分析"
outline:
  draft_prompt: "提取 ds_vibration 的结论，用一句话概括主轴承状态"
  
  # ★ 新增：AI 生成的报告初稿，被解析为一个默认文本区块
  original_blocks:
    - id: "blk_1"
      type: "text"
      content: "当前设备主轴承振幅为 8.5mm/s，超过 7.0 的告警阈值，存在高频振动风险。"

content:
  # (与上方阶段一完全一致，只含 2 个 dataset 和 1 个 layout)
  datasets: ...
  presentation: ...
```

---

## 阶段三：用户修改定稿态 (User Edited & Mutated)
**场景**：用户在 Web 页面上修改了大纲初稿文本，点击保存正式生成报告。由于修改既包含了“现场无中生有的新事实（漏油）”，也包含对报告排版增减的“强意图（加个折线图）”，系统触发 Template Copilot Agent 拦截了这次保存行为，生成了重构后的“终极形态”。

**结构特征（Diff 核心所在）**：
- `outline` 收到了 `user_blocks` 数组。这里不仅包含了用户修改过的 `type: text` 区块，还包含了一个由前端使用 Notion 式 `/chart` 命令生成的 `type: intent` 具体意图区块。
- Agent 在对比 `user_blocks` 与 `original_blocks` 后：
  1. 发现 `blk_1` 文本被加上了一句漏油评价 -> 将其外挂给 `ai_synthesis`。
  2. 发现新增了 `blk_2 (chart)` 意图 -> 推生出了 `nl2sql` 数据池及配套图表区块。

```yaml
title: "3.2 主轴承运行状态分析"
outline:
  draft_prompt: "提取 ds_vibration 的结论，用一句话概括主轴承状态"
  original_blocks: [ ... ]
  
  # ★ 新增：用户在富文本和组件混合界面下的定稿产物
  user_blocks:
    - id: "blk_1"
      type: "text"
      content: "当前设备主轴承振幅为 8.5mm/s，现场已发现主轴端盖漏油。"
    - id: "blk_2"
      type: "intent"
      command: "chart"
      content: "补充近 3 天的振动趋势折线图"

content:
  datasets:
    # ── 1. 原有的基础数据维持不变，不篡改客观真理 ──
    - id: "ds_vibration"
      # ...
      
    # ── 2. [由 Agent 扩长] 自动针对用户的排版要求，生成万能兜底数据池 ──
    - id: "ds_dynamic_vib_trend_agent_injected"
      source:
        kind: nl2sql
        description: "查询设备 {$device} 最近 3 天的振动曲线历史数据"
        
    # ── 3. [由 Agent 修改] 原有的 AI 综合诊断被篡改：将“漏油”挂为附加条件 ──
    - id: "ds_synthesis"
      depends_on: ["ds_vibration"]
      source:
        kind: ai_synthesis
        # ... 知识请求中增加了对漏油的探索
        knowledge:
          params: { symptoms: "振幅过高，漏油" }
        prompt: |
          请依据测点数据评估故障。
          【来自用户的现场补充事实，务必纳入考量：现场已发现主轴端盖漏油。】

  presentation:
    type: composite_table
    columns: 8
    sections:
      # ── 1. 保留原本的文字结论坑位 ──
      - band: "振动诊断结论"
        # ...
          
      # ── 2. [由 Agent 新增] 给用户硬加出来的占位 ──
      - band: "近 3 天振动趋势 (基于用户意图动态扩充)"
        dataset_id: "ds_dynamic_vib_trend_agent_injected"
        layout:
          type: chart
          chart_type: "line"
```

## 树结构对比总结

| 维度 | 阶段一：纯模板态 | 阶段二：未修改草稿态 | 阶段三：用户定稿修改态 |
|---|---|---|---|
| **`outline` 节点** | 仅含配置指令 | 获得初版区块列阵 (`original_blocks`) | 留存用户终稿的混合区块 (`user_blocks`) 供 Agent 进行结构化解析 |
| **`datasets` (客观数据)** | 固定 SQL，静态绑定 | 固定 SQL，静态绑定 | SQL 保持不篡改，同时扩充 `nl2sql` 数据池满足增量数据意图需求 |
| **主观诊断融合** | 纯从客观数据得出评价 | 同阶段一 | Agent 将用户的游离闲聊作为附加 Context 融合进了 `prompt` 中 |
| **UI 呈现布局** | 原模板中定义了多少块就是多少 | 原封不动 | 动态生成了与新数据池对应的新 `section` 区块 |
