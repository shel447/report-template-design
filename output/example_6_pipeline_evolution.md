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

---

## 场景四：基于对话生成的定时巡检报告 (麦当劳 IT 基础设施健康评估)

**业务述求**：店长通过对话系统发语：“请帮我生成一份每周二的设备巡检报告”。这要求系统不仅能解析出报告对象，还能将大纲意图与 **Schedule 定时调度**、相对时间派生完美结合。

### 📌 State 0: 原始空模板
```yaml
id: "tpl_mcd_equipment"
name: "园区核心 IT 与网络设备巡检"
parameters:
  - id: "report_cycle"
    label: "报告周期"
    input_type: "enum"
    options: ["每天", "每周二", "每月"]
    interaction_mode: "chat"
  - id: "analysis_period"
    label: "数据回溯范围"
    type: "time_range" 
    derive_from: "T_biz" # ⬅️ 声明绑定至定时任务执行时的业务基准时间 (解决时间联动问题)
    snap: "week"         # 对齐到上一个整周
    hidden: true
```

### 📌 State 1 & State 2: 意图捕获与大纲实例化
对话系统的 NLP 捕捉到了 `每周二` 的周期要求，准备向 Scheduler 发起定时任务注册。同时组装了针对该巡检的大纲蓝图：
```yaml
parameters:
  - id: "report_cycle", value: "每周二"   # ⬅️ 触发了后台 Scheduler 注册逻辑
  - id: "analysis_period", value: "近一周" # 派生自调度触发时机

sections:
  - title: "园区核心 IT 设施健康周报"
    outline:
      document: |
        全面检查园区核心设施（包含：{@dev1}、{@dev2}、{@dev3}）在 {@period} 内的健康状态。
        如有连续处于高温警告区超过 {@threshold} 的设备，请单独生成【预警维护清单】。
      blocks:
        - id: "dev1", type: "free_text", value: "数通设备"
        - id: "dev2", type: "free_text", value: "服务器"
        - id: "dev3", type: "free_text", value: "协作设备"
        - id: "period", type: "param_ref", value: "{$analysis_period}"
        - id: "threshold", type: "threshold", value: "30分钟"
```

### 📌 State 3: Agent 编译底层逻辑（等待每周二跑批）
Agent 准确识别除了常规的健康概览外，还需要一个带异常阈值的过滤表（预警维护清单）。
```yaml
sections:
  - title: "园区核心 IT 设施健康周报"
    content:
      datasets:
        - id: "ds_health_overview"
          source: { kind: sql, query: "SELECT device, avg_temp, status FROM mcd_it_infra_logs WHERE device IN ('数通设备', '服务器', '协作设备') AND time >= $T_data_start" }
        - id: "ds_warning_list"
          source: { kind: sql, query: "SELECT device, overtemp_duration FROM mcd_it_infra_logs WHERE overtemp_duration > 30 AND time >= $T_data_start" }
      
      presentation:
        type: composite_table
        sections:
          - band: "核心 IT 设备健康概况"
            dataset_id: "ds_health_overview"
            layout: { type: kv_grid, cols_per_row: 3 }
          - band: "预警维护派单 (机房连续高温 > 30分钟)"
            dataset_id: "ds_warning_list"
            layout: { type: simple_table }
```
*(证明结果：不仅包含丰富多维的意图降维，且时间范围变量 `$T_data_start` 被推迟到每周二引擎跑批时，再按实际算出的相对基准 `T_biz` 现场绑定注入，实现了对话系统下达“每周二执行的定时巡检任务”的闭环过渡。)*

---

## 场景五：跨组织的多模块运维分析 (金拱门中国网络运行诊断)

**业务述求**：IT 总监通过对话界面诉求：“请帮我生成金拱门（中国）有限公司的运维分析报告，包括雅居乐国际广场餐厅、上海体育场餐厅近一周的运维情况，内容包含网络中断情况、园区出口带宽、topN流量应用等。”

### 📌 State 0: 原始网络运维空模板
```yaml
id: "tpl_net_op"
name: "企业园区网络运维分析"
parameters:
  - id: "company"
    label: "目标公司"
    input_type: "free_text"
  - id: "store_list"
    label: "餐厅列表"
    input_type: "dynamic"
    multi: true         # ⬅️ 允许多值以支持多个餐厅横向比对
```

### 📌 State 1 & State 2: 超长复杂提示词下的参数与意图提取
对话系统的 Agent 将这句超长诉求拆分为两部分：实体放入全局 Parameter 框，具体“查什么”则写入各个裂变的对应章节大纲。
```yaml
parameters:
  - id: "company", value: "金拱门（中国）有限公司"
  - id: "store_list", value: ["雅居乐国际广场餐厅", "上海体育场餐厅"]

sections:
  - title: "{$company} - 门店网络状况"
    foreach: { param: "store_list", as: "store" } # 检测到多个门店实体，自动进入裂变体系
    outline:
      document: |
        分析门店 {@store_name} 近一周的网络运维情况。
        核心版块必须包含：1. {@m1}情况； 2. {@m2}走势； 3. {@m3}排名。
      blocks:
        - id: "store_name", type: "param_ref", value: "{$store}"
        - id: "m1", type: "indicator", value: "网络中断"
        - id: "m2", type: "indicator", value: "园区出口带宽"
        - id: "m3", type: "indicator", value: "topN流量应用"
```

### 📌 State 3: 顶层宏观大纲被编译为多维度数据矩阵
底层系统的 Compiler Agent 会针对这三大关键诉求（中断、带宽、排名），利用其常识推断并独立构建 3 个不同的 dataset，同时为其精心配置最匹配的图形渲染器组件。
```yaml
sections:
  - title: "{$company} - 门店网络状况"
    content:
      datasets:
        - id: "ds_interruptions"
          source: { kind: sql, query: "SELECT count, duration_sum FROM net_alerts WHERE type='中断' AND store_id='{$store}'" }
        - id: "ds_bandwidth"
          source: { kind: sql, query: "SELECT time, bw_usage FROM net_metrics WHERE metric='出口带宽' AND store_id='{$store}'" }
        - id: "ds_top_n_app"
          source: { kind: sql, query: "SELECT app_name, bytes FROM net_flow WHERE store_id='{$store}' ORDER BY bytes DESC LIMIT 5" }
          
      presentation:
        type: composite_table
        sections:
          - band: "可靠性：网络中断与可用性概况"
            dataset_id: "ds_interruptions"
            layout: { type: kv_grid, cols_per_row: 2 } # ⬅️ Agent判断：中断类概括聚合指标，适合使用大字卡片呈现
          - band: "容量性能：园区出口带宽趋势图"
            dataset_id: "ds_bandwidth"
            layout: { type: chart, chart_type: "line" } # ⬅️ Agent判断：随着时间推移的带宽必须展示时序规律，使用折线图
          - band: "应用质量：TopN 业务流量应用排名"
            dataset_id: "ds_top_n_app"
            layout: { type: chart, chart_type: "bar" } # ⬅️ Agent判断：TopN 类的离散实体对比排名天生适合柱状图！
```
*(证明结果：无论该高管在对话时的诉求包含多少个参差不齐的数据维度特征（中断是布尔与次数，带宽是曲线，排名是柱榜），大纲蓝图的作用就是将其统一“降服”为一段清爽的多插槽意图文本。而接水管的人——底层 Agent，就像组装高级工业乐高一样，非常严谨地对它们发起了分离查询，并赋予最科学合理的 UI 图展示方案。最终通过 `foreach` 实现了所有目标门店的横向大联防巡检！)*
