# 大纲即蓝图验证：单向编译器架构 (Blueprint Compiler)

根据最新的架构设计，“大纲（Outline）”被严格定义为**报告生成的指令蓝图**，不再包含任何诸如“8.5mm/s”由于运行 SQL 而取得的实体数据结果。
取而代之的是，大纲本身就是通过 UI 界面组织的 **“意图区块 (Intent Blocks)”**，用来告诉后台：这里该查个折线图、这里该填个单一数值测点汇总、这里该交给 AI 总结。

我们通过 `[大纲蓝图] -> (Agent静态编译) -> [底层高度严谨的数据与展示结构]` 的流程，真正实现了所见即所得的极高操作上限以及底线安全的结构隔离。

---

## 侧层比对：蓝图态 VS 编译态

以下演示 `example_5_wysiwyg_outline.yaml` 例子中的映射关系结构：

### 一、用户的交互视角（输入：大纲蓝图）
在这个环节，没有任何实际连接数据库和数据结果。
```yaml
outline:
  document: |
    当前设备主轴承的运行基本情况如下。当前振动幅值为：{@blk_metric_vib}。
    综合诊断结论如下：
    {@blk_ai_diag}
    
    【附录】近期辅助分析趋势图：
    {@blk_chart_trend}
    
  blocks:
    - id: "blk_metric_vib"
      type: "metric"   # ⬅️ 在 UI 上强约束占位符
      intent: "查询设备当前最近一次跑批的振动幅值"
      
    - id: "blk_ai_diag"
      type: "ai_summary" # ⬅️ 生成摘要区块
      intent: "结合近期告警流水，评估轴承是否存在高频损坏风险，并注意现场已知有轻微漏油现象"
      
    - id: "blk_chart_trend"
      type: "chart"    # ⬅️ 图形意图
      intent: "展示近 3 天的振动趋势折线图，用于辅助证明上述结论"
```

### 二、Agent (Template Copilot) 的后台工作
当用户保存上述蓝图时，Agent 开始对其进行降维翻译：
1. 它读到 `blk_metric_vib`，决定创建一个提取指标的 `nl2sql` 数据池。
2. 它读到 `blk_ai_diag`，决定创建一个 `ai_synthesis` 数据池，并且将这个意图内容填入该数据池的 prompt。
3. 它读到 `blk_chart_trend`，立刻创建一个取日期的 `nl2sql` 数据池，并在 `presentation` 中补入一个 `chart(line)` 组件将数据吃进来。

### 三、底层架构的视角（输出：编译后可跑批实例）
```yaml
content:
  datasets:
    # Agent 响应意图自动翻译出的 3 个取数逻辑
    - id: "ds_metric_vib"
      source: { kind: nl2sql, description: "查询设备当前最近一次..." }
    - id: "ds_trend_chart"
      source: { kind: nl2sql, description: "展示近 3 天的振动..." }
    - id: "ds_synthesis"
      source: { kind: ai_synthesis, prompt: "结合..., 漏油现场..." }

  presentation:
    type: composite_table
    columns: 8
    sections:
      # 响应纯文本与指标、AI结论合并显示的区块
      - band: "振动诊断结论"
        layout: { type: kv_grid, dataset_id: "ds_synthesis" }
        
      # Agent 根据 Chart 意图翻译出的视图壳子
      - band: "辅助分析趋势图"
        layout: { type: chart, chart_type: "line", dataset_id: "ds_trend_chart" }
```

## 优势总结
1. **数据绝不“幻觉”**：用户随便在大纲里写“我要看昨日故障率”，那句话仅作为编译 Prompt 创建了 `nl2sql`。假如底层确实查不出数据，底层只是空表，绝不会凭空瞎造出 8.5mm/s 的内容混入。
2. **UI 支撑力度满级**：前端根据 `type: metric`、`type: chart` 生成特定的组件，让用户的“大纲编辑”天然就像 Notion 搭建仪表盘的交互，彻底告别了“修改纯文本测大模型智商”的极高风险与不确定性。
