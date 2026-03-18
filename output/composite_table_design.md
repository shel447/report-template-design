# 复合表格模板设计规范

> 版本 v2.0 | 2026-03-18

---

## 一、核心模型

复合表格以「**局部数据池 + 列网格 + 分区段**」为基础构建：

```
content
  ├── datasets[]     局部数据池（数据获取层，与 presentation 平级）
  │     ├── id         数据集唯一标识
  │     ├── depends_on 前置依赖数据集 id 列表（构成局部 DAG）
  │     └── source     数据来源声明（sql / nl2sql / ai_synthesis）
  │
  └── presentation   视图呈现层（与 datasets 平级）
        ├── type: composite_table
        ├── columns    整体列网格宽度（逻辑列数）
        └── sections[] 分区段列表
              ├── band        可选，区段标题行（自动 colspan=全宽）
              ├── layout      行布局模式（见下节）
              └── dataset_id  绑定局部数据池中的数据集
```

> **作用域约束**：`datasets` 及其 `depends_on` / `refs` 仅限于当前 `content` 节点内部生效，不允许跨章节引用。

---

## 二、局部数据池（datasets）

### 2.1 数据集定义

```yaml
datasets:
  - id: "ds_base"                    # 必填，当前 content 内唯一
    source:
      kind: sql | nl2sql | ai_synthesis
      # …… source 专属字段见第三节
      
  - id: "ds_summary"
    depends_on: ["ds_base"]          # 声明依赖，引擎按 DAG 拓扑排序执行
    source:
      kind: ai_synthesis
      # ……
```

### 2.2 局部 DAG 执行规则

1. 引擎解析 `datasets`，按 `depends_on` 构建有向无环图（DAG）。
2. **无依赖**的数据集立即并发执行。
3. **有依赖**的数据集等待所有前置数据集就绪后再执行。
4. 执行完成后，各区段（sections）的渲染按声明顺序进行。

---

## 三、数据来源（source.kind）

| `kind` | 关键字段 | 说明 |
|---|---|---|
| `sql` | `query` | 直接执行参数化 SQL，支持 `{param}` / `{$var}` 占位符 |
| `nl2sql` | `description` | 自然语言描述 → LLM 生成 SQL → 执行 |
| `ai_synthesis` | `context`, `knowledge`, `prompt` | 多源上下文（refs+queries）+ RAG 知识检索 + LLM 合成 |

### 3.1 ai_synthesis 专属字段

```yaml
source:
  kind: ai_synthesis
  context:
    refs: ["ds_base", "ds_extra"]    # 引用同 content 内已就绪的数据集结果
  knowledge:
    query_template: "针对 {subject} 的 {symptoms} 提供诊断建议"
    params:
      subject: "{device_model}"       # 支持参数占位符与 refs 路径表达式
      symptoms: "refs.ds_base[status='异常'].name"
      objective: "获取故障诊断与维修建议"
  prompt: |                           # LLM 提示词模板
    请根据以下上下文和知识库信息进行综合评估……
```

### 3.2 知识检索输入三要素

| 要素 | 字段 | 说明 |
|---|---|---|
| **Subject（主体）** | `params.subject` | 设备型号、关键组件名 |
| **Symptoms（征兆）** | `params.symptoms` | 当前异常测点、告警码，支持 refs 路径表达式动态提取 |
| **Objective（目标）** | `params.objective` | 期望的回答类型（诊断、维修指导、预警等级等） |

---

## 四、布局模式

**布局模式只有两种**，覆盖所有实际场景：

| `layout.type` | 适用场景 | 特点 |
|---|---|---|
| `kv_grid` | 标签-值对（基本信息、结论区）| 每行排 N 对，key/value 各有固定 span |
| `tabular` | 明细数据、指标列表 | 自定义列头 + 多行结果 |

> `kv_grid` 当 `cols_per_row: 1` 时即全宽键值对，不需要单独类型。

---

## 五、kv_grid 布局

```yaml
layout:
  type: kv_grid
  cols_per_row: 2      # 每行几对 KV（约束：(key_span+value_span)*cols_per_row = columns）
  key_span: 1          # 标签格占几列
  value_span: 3        # 值格占几列
  dataset_id: "ds_xxx" # 绑定数据集（无绑定时纯静态）
```

### 数据填充方式（三种，可混用）

| 方式 | 配置 | 说明 |
|---|---|---|
| **参数/静态** | `fields[].value: "{param}"` | 直接替换全局参数或 foreach 变量 |
| **SQL 单行** | `fields[].col` + `dataset_id` | 数据集返回一行，按列名取值 |
| **SQL 动态 KV** | `dataset_id` + `key_col`/`value_col` | 数据集返回多行，每行成一个 KV 对 |

```yaml
# 方式一：参数直填（无需 dataset_id）
fields:
  - key: "设备名称"
    value: "{device_name}"

# 方式二：数据集单行，按列名映射
dataset_id: "ds_base_info"
fields:
  - key: "设备名称"
    col: "name"
  - key: "安装位置"
    col: "location"

# 方式三：数据集动态 KV（key 也来自数据库）
# 在 datasets 中声明：
#   source:
#     kind: sql
#     query: "SELECT attr_name, attr_value FROM device_attrs …"
#     key_col: "attr_name"
#     value_col: "attr_value"
# 在 layout 中：
dataset_id: "ds_device_attrs"   # 引擎自动按 key_col/value_col 展开 KV
```

---

## 六、tabular 布局

```yaml
layout:
  type: tabular
  dataset_id: "ds_metrics"        # 绑定数据集
  headers:                         # 列头声明，span 总和必须等于 columns
    - label: "指标名"
      span: 2
    - label: "当前值"
      span: 2
    - label: "~dynamic~"           # 特殊标记：从 SQL PIVOT 结果自动展开列头
      span: 1
      repeat: true
  columns:                         # 数据列映射，需与 headers 一一对应
    - field: "metric_name"
      span: 2
    - field: "current_value"
      span: 2
    - field: "~dynamic~"           # 同上，自动映射 PIVOT 结果的每列
      span: 1
      repeat: true
```

---

## 七、完整字段结构

```yaml
content:

  # ── 局部数据池（与 presentation 平级）──
  datasets:
    - id: "ds_A"
      source:
        kind: sql
        query: "…"
    - id: "ds_B"
      source:
        kind: nl2sql
        description: "…"
    - id: "ds_C"
      depends_on: ["ds_A", "ds_B"]
      source:
        kind: ai_synthesis
        context:
          refs: ["ds_A", "ds_B"]
        knowledge:
          params:
            subject: "…"
            symptoms: "…"
            objective: "…"
        prompt: "…"

  # ── 视图呈现（与 datasets 平级）──
  presentation:
    type: composite_table
    columns: 8
    sections:
      - band: "区段标题"            # 可选，null 表示无标题行
        layout:
          type: kv_grid | tabular
          dataset_id: "ds_A"       # 绑定局部数据集
          # …… layout 专属字段
```

---

## 八、约束规则

1. `(key_span + value_span) × cols_per_row` 必须等于 `columns`（kv_grid）
2. `tabular` 中 `headers[].span` 之和必须等于 `columns`
3. `band` 行自动 `colspan=columns`，不需单独声明
4. `kv_grid` 的 `fields` 若数量不能被 `cols_per_row` 整除，最后一行以空白补齐
5. `tabular` 的 `dataset_id` 必填；`kv_grid` 的 `dataset_id` 与 `fields[].value` 二选其一或混用
6. `ai_synthesis` 的 `refs` 所引用的数据集必须在同一 `content` 的 `datasets` 中，且其 `depends_on` 已声明对应依赖
7. `datasets` 的依赖图（DAG）不能有环，检测到环时报错拒绝渲染
