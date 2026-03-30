# 智能报告模板系统 — 设计文档

> 版本：v2.0 | 日期：2026-03-18

---

## 一、概述

智能报告系统通过预置的**报告模板**，结合用户交互提取的参数，自动生成结构化报告文档。

### 整体流程

```
用户交互
  → 匹配报告类型 & 场景
  → 系统从对话中提取参数
  → 提醒补全缺失的必填参数
  → 所有必填参数就绪后
  → 填充模板 → 生成报告
```

---

## 二、模板分类体系

模板按两级维度组织：

| 层级 | 字段 | 说明 |
|---|---|---|
| 报告类型 | `type` | 顶层分类，可扩展，如：设备健康评估、设备运行状态 |
| 场景 | `scene` | 同类型下的细分，如：总部、分部 |

---

## 三、参数系统

每个模板定义一组参数（`parameters`），所有参数在解析阶段统一收集，完成后集中注入内容。

### 参数属性

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 参数唯一标识，在内容中以 `{param_id}` 方式引用 |
| `label` | string | 用户可读的参数名称 |
| `required` | boolean | 是否必填 |
| `input_type` | enum | 输入方式，见下表 |
| `multi` | boolean | 是否允许多值，`true` 时该参数可作为 `foreach` 的来源 |
| `options` | array | 枚举值列表，仅 `input_type: enum` 时使用 |
| `source` | string | 动态选项来源，仅 `input_type: dynamic` 时使用 |

### `input_type` 枚举

| 值 | 说明 |
|---|---|
| `free_text` | 用户自由输入 |
| `enum` | 从预设选项中选择 |
| `dynamic` | 从外部来源（接口/查询）动态获取选项 |

---

## 四、章节结构

### 4.1 基本层级

报告内容以 `sections` 字段描述，支持**递归嵌套**（`subsections`），对应报告的目录与章节层级。

```
sections[]
  ├── title        章节标题（支持 {param} 占位符）
  ├── foreach      可选，循环展开声明（见 4.2）
  ├── outline      可选，参数化意图大纲蓝图（见 4.3）
  ├── content      可选，当前节点的内容（叶节点）
  └── subsections  可选，子章节（中间节点）
```

> 一个节点 `content` 与 `subsections` 互斥：有子章节则不直接挂内容。

### 4.2 参数驱动的章节循环 (foreach)

当某个参数 `multi: true` 且有多个值时，可用 `foreach` 将某个章节按该参数的每个取值**重复展开**。

```yaml
foreach:
  param: "device_ids"   # 绑定的多值参数 id
  as: "device"          # 迭代变量名，内容中以 {$device} 引用
```

- 迭代变量用 `{$varname}` 前缀，与全局参数 `{param}` 区分
- 若绑定参数实际只有一个值，退化为正常单次渲染
- 暂不支持嵌套 `foreach`

**展开示意**（`device_ids = [A001, A002]`）：

```
2. 各设备详细分析
   2.1 设备 A001 运行概况
   2.2 设备 A001 异常记录
   2.3 设备 A002 运行概况
   2.4 设备 A002 异常记录
```

### 4.3 `outline`（参数化意图大纲与单向编译）

为了支持用户在正式渲染前进行直观的高层干预（WYSIWYG），我们在 `sections` 增加了 `outline`（大纲蓝图）模型。
**大纲的本质是"一段带参数的意图描述"，而非"最终报告的布局草稿"**。

在编辑器前端，大纲表现为一段完整的**连贯富文本流 (document)** 加上附随的**意图参数列阵 (blocks)**。
用户在书写自然流畅的意图描述时，可通过类似 Notion 的 `/` 命令注入可变参数占位符（语法形如 `{@block_id}`）。这些占位符在 `blocks` 数组中被定义为**意图的参数**——它们约束的是"分析什么"、"看多长时间"、"关注哪台设备"：

*   `indicator`（指标选择）：UI 上呈现为指标下拉选择器，限制用户只能选取一个合法的监测指标名称。
*   `time_range`（时间范围）：UI 上呈现为日期/时间跨度选择器。
*   `scope`（范围/设备）：UI 上呈现为设备或资产范围选择器。
*   `free_text`（自由文本）：允许用户补充现场观察等开放性信息。
*   `param_ref`（参数引用）：直接引用模板全局参数（如 `{$device}`）。

> **关键区分**：block 描述的是"意图的变量部分"，而不是"最终报告放什么图表"。至于报告最终用折线图还是表格来展示——那是 Agent 编译时根据整体意图自主决策的事情。

举个例子，用户看到的大纲是这样一句连贯的话：
> 对设备 `{@target_device}` 的 `{@focus_metric}` 进行深度分析，分析范围为 `{@analysis_period}`，如有异常请结合 `{@supplementary_context}` 给出诊断建议。

#### "模板编译官" (Template Copilot) 工作流
当用户在前端调整完意图描述和这些参数后点击保存：
1. **[蓝图提交]**：系统将 `document` 整句意图文本及填好值的 `blocks` 参数发给后端大模型 Agent。此时尚未查库，没有任何客观数值产生。
2. **[意图降维编译]**：Agent (Template Copilot) 作为编译器，通读整段意图描述，**自主决策**底层实现方案：
   - Agent 判断"深度分析振动幅值" → 生成取当前值的 `nl2sql` 数据集 + 取历史趋势的 `nl2sql` 数据集。
   - Agent 判断"关注异常波动趋势" → 自主决定用折线图来呈现，配出 `presentation` 中的 `chart` 组件。
   - Agent 判断"结合漏油给出诊断建议" → 生成 `ai_synthesis` 节点，并将漏油信息融入 prompt。
3. **[固化模板]**：编译后的模板被保存。
4. **[运行时渲染]**：生产引擎 (Data Engine) 每月跑批时，拉取这个固化好的模板，连接正式数据库，拉取真实数据（如"振幅=8.5mm/s"），生成最终报告。

这种 `[参数化意图] -> (Agent自主编译) -> [严谨配置] -> (引擎运行) -> [结果报告]` 的模式，完美做到了高灵活性交互与底层数据严谨性的解耦隔离。具体可见 [`example_5_wysiwyg_outline.yaml`](output/example_5_wysiwyg_outline.yaml)。

---

## 五、内容节点类型系统

内容节点（`content`）将**数据获取**与**呈现布局**分离为两个**平级**维度。

### 5.1 内容节点结构

```
content
  ├── datasets[]      局部数据池（数据获取层）
  │     ├── id          数据集唯一标识
  │     ├── depends_on  前置依赖数据集 id 列表（构成局部 DAG）
  │     └── source      数据来源声明
  │
  └── presentation    视图呈现层
        ├── type        呈现类型
        └── ...         类型专属字段
```

> `datasets` 与 `presentation` 在 `content` 下平级存在。`datasets` 的作用域仅限当前 `content` 节点内部，不允许跨章节引用。

### 5.2 数据来源（source.kind）

| `kind` | 说明 |
|---|---|
| `sql` | 直接执行预定义 SQL，参数作为条件或列 |
| `nl2sql` | 自然语言描述 → LLM 生成 SQL → 执行 |
| `ai_synthesis` | 多源上下文引用 + RAG 知识检索 + LLM 合成（用于总结性内容） |
| 无 source | 纯静态内容，`type: text` 时使用 |

### 5.3 局部 DAG 执行机制

当一个 `content` 包含多个 `datasets` 时，引擎根据 `depends_on` 构建局部有向无环图（DAG）：

1. 无依赖的数据集可**并发执行**
2. 有依赖的数据集等待所有前置数据集就绪后再执行
3. 检测到环时报错拒绝渲染

```yaml
datasets:
  - id: "ds_metrics"          # 无依赖，立即执行
    source: { kind: sql, ... }
  - id: "ds_faults"           # 无依赖，与 ds_metrics 并发
    source: { kind: sql, ... }
  - id: "ds_summary"
    depends_on: ["ds_metrics", "ds_faults"]  # 等待前两者
    source: { kind: ai_synthesis, ... }
```

### 5.4 ai_synthesis 专属字段

```yaml
source:
  kind: ai_synthesis
  context:
    refs: ["ds_metrics", "ds_faults"]   # 引用同 content 内已就绪的数据集
  knowledge:                             # 知识检索（RAG）
    query_template: "..."
    params:
      subject: "{device_model}"          # 主体：设备型号、关键组件
      symptoms: "refs.ds_metrics[...]"   # 征兆：当前异常指标
      objective: "..."                   # 目标：期望获取的回答类型
  prompt: "..."                          # LLM 提示词模板
```

### 5.5 呈现形式（presentation.type）

| `type` | 说明 |
|---|---|
| `text` | 纯静态段落，参数占位符直接替换 |
| `value` | SQL 返回单一值，嵌入锚点文本的 `{$value}` 位置 |
| `chart` | 可视化图形，`chart_type` 指定图形类型 |
| `simple_table` | 普通二维表格 |
| `composite_table` | 复合表格，支持多区段、合并列、动态列（详见 [`composite_table_design.md`](./output/composite_table_design.md)） |

### 5.6 合法组合矩阵

| source.kind | presentation.type | 备注 |
|---|---|---|
| 无 | `text` | 纯静态文本 |
| `sql` | `value` | 单值填入锚点 |
| `sql` | `simple_table` | 标准结果集表格 |
| `sql` / `ai_synthesis` | `composite_table` | 复合表格，数据与布局平级解耦 |
| `sql` | `chart` | 已知维度统计图 |
| `nl2sql` | `chart` | LLM 推断图类型 |
| `nl2sql` | `simple_table` | LLM 查询结果表 |

> `composite_table` 通过 `datasets` 机制支持 `sql`、`nl2sql`、`ai_synthesis` 三种来源混合使用。

---

## 六、占位符约定

| 语法 | 含义 |
|---|---|
| `{param_id}` | 引用全局参数值 |
| `{$varname}` | 引用 `foreach` 迭代变量当前值 |
| `{$value}` | `presentation: value` 中引用 SQL 返回的单值 |
| `{@block_id}` | 引用大纲 `outline` 中的意图参数占位符 |
| `refs.ds_id.field` | `ai_synthesis` 中引用同 content 内数据集的字段 |

---

## 七、Schema 与示例

- JSON Schema：见 [`template.schema.json`](./template.schema.json)
- 完整模板示例：见 [`example_device_health_hq.yaml`](./example_device_health_hq.yaml)
- 复合表格设计规范：见 [`composite_table_design.md`](./output/composite_table_design.md)
- 复合表格示例集：见 [`output/examples_overview.md`](./output/examples_overview.md)
