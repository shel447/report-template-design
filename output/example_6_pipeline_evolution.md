# 智能报告模板系统 - 宏观架构演化证明示例 (v2.0)

本文档通过 **3 个典型的真实工业场景**，详细推演了一个报告模板（Template）在系统内是如何从**最初的空骨架**，一步步历经参数填充、大纲编辑，最终被 Agent 编译为**底层运行结构**的完整生命周期。

生命周期的 4 个核心状态：
1. **State 0 (空模板态)**：模板库里的原始配置，纯骨架结构。
2. **State 1 (已实例化态)**：系统或对话流收集了用户填写的全局参数。
3. **State 2 (大纲蓝图态)**：用户在富文本界面中完成了带着“受控参数插槽”的业务述求编写 (WYSIWYG)。
4. **State 3 (底层编译态/运行态)**：大模型 Agent 读懂了 State 2 的大纲，将其转换为了底层数据获取 (datasets) 与组件排版 (presentation) 的严谨机器骨架。

---

## 场景一：单指标超阈值追查诊断 (Simple Condition Dispatch)

**业务述求**：查某设备的特定指标，并设定一个门槛。如果超出了这个门槛，就去查它的异常明细日志。

### 📌 State 0: 最原始的模板定义 (空模板)
只定义了标题框架和需要的全局参数。
```yaml
id: "tpl_asset_health"
name: "单设备异常诊断简报"
parameters:
  - id: "target_asset"
    label: "分析目标设备"
    required: true
    input_type: "dynamic"
    source: "/api/devices"
    interaction_mode: "chat"

sections:
  - title: "异常诊断报告 - {target_asset}"
    # 大纲蓝图和机器执行逻辑目前完全空缺，等待实例化
```

### 📌 State 1: 填了参数之后的实例化状态
当用户通过对话输入“帮我查一下 A01 离心泵”时，系统提取出参数，生成一个实例大纲：
```yaml
id: "instance_5589a"
parameters:
  - id: "target_asset"
    value: "A01 离心泵"   # ⬅️ 参数就位

sections:
  - title: "异常诊断报告 - A01 离心泵"
    outline:
      # 此时生成了一段系统默认的范例意图文本 (Default Blueprint)
      document: "请分析设备 {@device} 的近期运行情况。"
      blocks:
        - id: "device"
          type: "param_ref"
          value: "{$target_asset}" # 自动绑定了被填入的全局参数
```

### 📌 State 2: 更新了大纲之后的模板状态 (WYSIWYG)
用户觉得默认大纲不够，在富文本界面上修改了大纲内容，并用 `/` 插入了指标、操作符、阈值等插槽。这是用户的强意图宣告：
```yaml
sections:
  - title: "异常诊断报告 - A01 离心泵"
    outline:
      document: |
        对设备 {@device} 的 {@metric} 进行深度排查。
        如果发现该指标 {@operator} {@threshold}，请立即列表展示出这些天的异常停机明细。
      blocks:
        - id: "device"
          type: "param_ref"
          value: "A01 离心泵"
        - id: "metric"
          type: "indicator"
          value: "出口压力"
        - id: "operator"
          type: "operator"
          value: "大于"
        - id: "threshold"
          type: "threshold"
          value: "1.2MPa"
```

### 📌 State 3: 最终用于生成报告的底层排版状态
Agent 读懂了 `如果 ... 大于 1.2MPa ... 请列表展示` 的意图逻辑，**自主决定**生成两段 SQL 数据源，并用一个键值对组件搭配一个表格来呈现。
```yaml
sections:
  - title: "异常诊断报告 - A01 离心泵"
    outline: { ... } # 保持不变，保留供下次编辑
    
    content:  # ⬅️ 引擎真正用来跑批执行的字节码！
      datasets:
        - id: "ds_pressure_overview"
          source: 
            kind: sql
            query: "SELECT current_pressure, status FROM ... WHERE asset='A01 离心泵'"
        
        - id: "ds_downtime_details" 
          # ⬅️ Agent 聪明地推断出了一张查明细的 SQL，并挂载了大于 1.2 的条件
          source: 
            kind: sql
            query: "SELECT start_time, reason, duration FROM downtime_logs WHERE asset='A01 离心泵' AND pressure > 1.2"
          
      presentation:
        type: composite_table
        sections:
          - band: "当前指标概况"
            dataset_id: "ds_pressure_overview"
            layout: { type: kv_grid, cols_per_row: 2 }
          - band: "异常停机追溯 (过滤条件：压力 > 1.2MPa)"
            dataset_id: "ds_downtime_details"
            layout: { type: simple_table }
```

---

## 场景二：结合人工现场批注的复杂能耗研判 (AI Synthesis)

**业务述求**：不仅要在报告里拉取客观数据宽表，还需要结合现场技工巡检看到的情况，让 AI 写综合结论段落。

### 📌 State 0: 原始模板定义
```yaml
id: "tpl_energy_eval"
name: "产线综合能耗评估"
parameters:
  - id: "line_id"
    label: "生产线选择"
    input_type: "enum"
    options: ["一期产线", "二期产线"]
    interaction_mode: "form"

sections:
  - title: "{line_id} - 综合能耗评估"
```

### 📌 State 1 & State 2: 填了参数并手写大纲的情况
假设管理员在界面上选了 `一期产线`，并且直接撰写了大纲蓝图，加入了一段“自己肉眼看到的自由文本补充”：
```yaml
sections:
  - title: "一期产线 - 综合能耗评估"
    outline:
      document: |
        调取 {@line} 近一个月的综合用电量及各班组分摊情况。
        现场排查情况补充记录：{@manual_insight}。请结合实际数据和现场情况，给出综合能耗批注。
      blocks:
        - id: "line"
          type: "param_ref"
          value: "一期产线"
        - id: "manual_insight"
          type: "free_text"
          value: "上周三夜班发生了变压器跳闸，且电容补偿柜有异响" # ⬅️ 这句话是数据库查不到的，但极其重要
```

### 📌 State 3: Agent 编译出的最终底层逻辑
这里展示了极强的解耦能力：Agent 会将查数据的指令编译交给 `sql` 处理，而将用户的 `free_text` (也就是跳闸异响之事) 动态织入 `ai_synthesis` 数据集的 Prompt 中。
```yaml
sections:
  - title: "一期产线 - 综合能耗评估"
    content:
      datasets:
        - id: "ds_power_matrix"
          source: { kind: nl2sql, description: "查询 一期产线 过去近一月各班组分摊的综合用电量" }
        
        - id: "ds_ai_diagnosis"
          depends_on: ["ds_power_matrix"]  # 必须等上一步耗电量查完
          source:
            kind: ai_synthesis
            context: { refs: ["ds_power_matrix"] } # 把客观数据喂给大模型分析
            prompt: |
              你是一个能耗专家。请基于以下查询到的实际班组用电数据进行异常分析。
              注意，现场人员补充了以下已知情况："上周三夜班发生了变压器跳闸，且电容补偿柜有异响"。
              请你在撰写综合能耗批注时，必须将此事实与能耗数据突变结合进行逻辑推演。
              
      presentation:
        type: composite_table
        sections:
          - band: "近一月班组耗电明细列表"
            dataset_id: "ds_power_matrix"
            layout: { type: simple_table } # 客观表格在前
          - band: "专家综合能耗批注"
            dataset_id: "ds_ai_diagnosis"
            layout: { type: text }         # AI 的研判结论在后
```

---

## 场景三：参数数组 foreach 无限裂变 (批处理架构伸缩)

**业务述求**：同时对比多个设备的表现。根据选中的多个设备，自动克隆同样的报告章节分别分析。

### 📌 State 0: 带有 foreach 声明的空模板
```yaml
id: "tpl_multi_pump"
name: "多泵体对比与单机下钻报告"
parameters:
  - id: "compare_devices"
    label: "对比设备集合"
    input_type: "dynamic"
    multi: true         # ⬅️ 划重点：此参数允许多选（数组）
    
sections:
  - title: "单机深度下钻分析 - {$device_item}"
    foreach:
      param: "compare_devices" # 绑定那个数组参数
      as: "device_item"        # 指代内部当前元素的迭代变量名
```

### 📌 State 1 & State 2: 填了三台设备并只写一次大纲
用户勾选了 `["Pump-A", "Pump-B", "Pump-C"]`。
同时，用户并不需要写三遍大纲，因为 State 2 的大纲是“模板级别的”，只需要写出一个“代表”。
```yaml
parameters:
  - id: "compare_devices"
    value: ["Pump-A", "Pump-B", "Pump-C"]   # 系统收集到了 3 个对象

sections:
  - title: "单机深度下钻分析 - {$device_item}"
    foreach: { param: "compare_devices", as: "device_item" }
    outline:
      document: "请以趋势图展现 {@pump} 在本月的 {@indicator} 数据表现情况。"
      blocks:
        - id: "pump"
          type: "param_ref"
          value: "{$device_item}" # ⬅️ 绑定父级的 foreach 迭代变量
        - id: "indicator"
          type: "indicator"
          value: "流量吞吐(m³/h)"
```

### 📌 State 3: 底层引擎运行时完全展开的状态 (Runtime Expanded)
*   **编译环节**：Agent 针对大纲（不论对象是谁），编译出 `nl2sql` 查流量和 `chart(line)` 画线的基础底座骨架。
*   **运行时环节**：Data Engine 介入，发现 `foreach` 需要循环 3 遍，立马就像“细胞分裂”一样平展出了 3 个实体 `content` 块。
*   向前端输出最终报告时，JSON 长这样：

```yaml
# 引擎运行时生成的完整内存结构：
sections:
  # ---------------- 裂变实例 1 ----------------
  - title: "单机深度下钻分析 - Pump-A"
    content:
      datasets:
        - id: "ds_flow_1"
          source: { kind: sql, query: "SELECT flow FROM ... WHERE asset='Pump-A' AND month='本月'" }
      presentation:
        type: composite_table
        sections: [{ dataset_id: "ds_flow_1", layout: { type: chart, chart_type: "line" } }]

  # ---------------- 裂变实例 2 ----------------
  - title: "单机深度下钻分析 - Pump-B"
    content:
      datasets:
        - id: "ds_flow_2"
          source: { kind: sql, query: "SELECT flow FROM ... WHERE asset='Pump-B' AND month='本月'" }
      presentation:
        type: composite_table
        sections: [{ dataset_id: "ds_flow_2", layout: { type: chart, chart_type: "line" } }]

  # ---------------- 裂变实例 3 ----------------
  - title: "单机深度下钻分析 - Pump-C"
    content: 
      datasets:
        - id: "ds_flow_3"
          source: { kind: sql, query: "SELECT flow FROM ... WHERE asset='Pump-C' AND month='本月'" }
      presentation:
        type: composite_table
        sections: [{ dataset_id: "ds_flow_3", layout: { type: chart, chart_type: "line" } }]
```
*(证明结果：通过参数域的 `multi` 和针对单体的 `outline`，引擎成功扩展出了可以动态缩放的自动化底层结构。即使勾选了 100 台设备，系统的开销与逻辑也仅仅是一次平滑铺开。)*
