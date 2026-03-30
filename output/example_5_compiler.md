# 大纲即参数化意图：单向编译器架构 (Blueprint Compiler)

根据最新的架构设计，"大纲（Outline）"被严格定义为**一段带参数的意图描述**。
大纲整体就是"意图"（想让报告做什么），而其中的 block 是这段意图中**可变的参数化部分**（分析哪个指标、看什么时间段、补充什么现场情况）。

**block 不规定最终报告的展现形式**（图表还是表格）——那是 Agent 编译时根据整体语义自主决策的事。

---

## 侧层比对：意图参数 VS 编译产物

以下演示 `example_5_wysiwyg_outline.yaml` 中的映射关系结构：

### 一、用户的交互视角（输入：参数化意图大纲）
没有任何数据库连接和数据结果。用户看到的是一句连贯的、可调参数的意图描述。
```yaml
outline:
  # 一句连贯的意图描述，{@...} 是用户可以调整的参数化插槽
  document: |
    对设备 {@target_device} 的 {@focus_metric} 进行深度运行状态分析。
    分析范围为 {@analysis_period}，重点关注是否存在异常波动趋势。
    如有异常，请结合 {@supplementary_context} 给出专业诊断及维护建议。

  # 意图参数定义（不涉及任何展现形式，只约束意图的变量部分）
  blocks:
    - id: "target_device"
      type: "param_ref"          # ⬅️ 引用全局参数
      hint: "指定本节分析的目标设备"
      default: "{$device}"
      
    - id: "focus_metric"
      type: "indicator"          # ⬅️ 指标选择器
      hint: "选择重点关注的监测指标"
      default: "振动幅值"
      
    - id: "analysis_period"
      type: "time_range"         # ⬅️ 时间跨度选择器
      hint: "指定分析时间跨度"
      default: "近3天"
      
    - id: "supplementary_context"
      type: "free_text"          # ⬅️ 开放性补充信息
      hint: "补充现场观察到的已知情况"
      default: "现场已知主轴端盖有轻微漏油现象"
```

### 二、Agent (Template Copilot) 的编译推理
当用户保存上述参数化意图后，Agent 通读整段 `document` + 填好的参数值，**自主决策**底层实现：
1. 读到"对...振动幅值进行深度分析" → 决定需要一个取振幅的 `nl2sql` 数据源。
2. 读到"分析范围为近3天" + "关注异常波动趋势" → 自主判断用折线图来展现趋势最合适。
3. 读到"结合...漏油现象给出诊断" → 决定需要一个 `ai_synthesis` 节点，并在 prompt 中融入漏油事实。
4. 最终自主选择 kv_grid + chart 的组合排版。

> **注意**：用户在大纲中没有指定任何图表类型或表格格式——这些全是 Agent 的编译产物。

### 三、底层架构的视角（输出：编译后可跑批实例）
```yaml
content:
  datasets:
    # Agent 自主翻译出的 3 个取数逻辑
    - id: "ds_vibration_current"
      source: { kind: nl2sql, description: "查询设备当前最近一次..." }
    - id: "ds_vibration_trend"
      source: { kind: nl2sql, description: "查询近 3 天的振动历史..." }
    - id: "ds_diagnosis"
      source: { kind: ai_synthesis, prompt: "深度分析... 漏油..." }

  presentation:
    type: composite_table
    columns: 8
    sections:
      # Agent 自主决定的排版方案
      - band: "振动诊断结论"
        layout: { type: kv_grid, dataset_id: "ds_diagnosis" }
      - band: "近期振动趋势"
        layout: { type: chart, chart_type: "line", dataset_id: "ds_vibration_trend" }
```

## 设计优势

1. **意图与展现彻底解耦**：用户只管"我想分析什么"，Agent 负责"怎么展示"。用户换一个 `focus_metric` 从"振动"改成"温度"，Agent 重新编译后可能决定换用表格而不是折线图——全程无需用户参与布局决策。
2. **UI 约束力精准**：`type: indicator` 让前端只渲染指标下拉框，`type: time_range` 只渲染日期选择器——用户的编辑行为被天然限制在合理范围内，不存在"乱写一通让 AI 猜"的问题。
3. **数据绝不"幻觉"**：大纲中没有任何真实数值，真实数据只在运行时由 Data Engine 查库产生。
