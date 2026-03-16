# 复合表格模板设计规范

> 版本 v1.0 | 2026-03-11

---

## 一、核心模型

复合表格以「**列网格 + 分区段**」为基础构建：

```
composite_table
  ├── columns        整体列网格宽度（逻辑列数）
  └── sections[]     分区段列表
       ├── band      可选，区段标题行（自动 colspan=全宽）
       ├── layout    行布局模式（见下节）
       └── source    可选，数据来源（sql / nl2sql）
```

**布局模式只有两种**，覆盖所有实际场景：

| `layout.type` | 适用场景 | 特点 |
|---|---|---|
| `kv_grid` | 标签-值对（基本信息、结论区）| 每行排 N 对，key/value 各有固定 span |
| `tabular` | 明细数据、指标列表 | 自定义列头 + SQL 多行结果 |

> `kv_grid` 当 `cols_per_row: 1` 时即全宽键值对，不需要单独类型。

---

## 二、kv_grid 布局

```yaml
layout:
  type: kv_grid
  cols_per_row: 2      # 每行几对 KV（约束：(key_span+value_span)*cols_per_row = columns）
  key_span: 1          # 标签格占几列
  value_span: 3        # 值格占几列
```

### 数据填充方式（三种，可混用）

| 方式 | 配置 | 说明 |
|---|---|---|
| **参数/静态** | `fields[].value: "{param}"` | 直接替换全局参数或 foreach 变量 |
| **SQL 单行** | `source.kind: sql` + `fields[].col` | SQL 返回一行，按列名取值 |
| **SQL 动态 KV** | `source.kind: sql` + `key_col`/`value_col` | SQL 返回多行，每行成一个 KV 对 |

```yaml
# 方式一：参数直填
fields:
  - key: "设备名称"
    value: "{device_name}"
  - key: "设备型号"
    value: "{device_model}"

# 方式二：SQL 单行，按列名映射
source:
  kind: sql
  query: "SELECT name, model, location, install_date FROM devices WHERE id='{device_id}'"
fields:
  - key: "设备名称"
    col: "name"
  - key: "设备型号"
    col: "model"
  - key: "安装位置"
    col: "location"
  - key: "投入时间"
    col: "install_date"

# 方式三：SQL 动态 KV（key 也来自数据库）
source:
  kind: sql
  query: "SELECT attr_name, attr_value FROM device_attrs WHERE device_id='{device_id}'"
  key_col: "attr_name"
  value_col: "attr_value"
```

---

## 三、tabular 布局

```yaml
layout:
  type: tabular
  headers:                    # 列头声明，span 总和必须等于 columns
    - label: "指标名"
      span: 2
    - label: "当前值"
      span: 2
    - label: "判断"
      span: 1
    - label: "说明"
      span: 3
  columns:                    # 数据列映射（必须与 headers 一一对应）
    - field: "metric_name"
      span: 2
    - field: "current_value"
      span: 2
    - field: "judgment"
      span: 1
    - field: "note"
      span: 3
source:
  kind: sql | nl2sql | ai_synthesis
  query: "..."              # sql 时写 query
  description: "..."        # nl2sql 时写自然语言描述
```

---

## 四、ai_synthesis 布局（新）

用于生成总结性、专家建议类内容。它不直接对应数据库字段，而是通过 AI 合成。

### 4.1 核心结构

```yaml
source:
  kind: ai_synthesis
  context:
    refs: ["section_id.field_id", ...]  # 引用报告内已有的数据节
    queries:                            # 额外的补充 SQL 查询
      - id: "history_alarm"
        query: "SELECT ..."
  knowledge:
    query_template: "针对 {model} 的 {symptom} 提供诊断建议"
    params:                             # 构造检索输入的三要素
      subject: "{device_model}"         # 主体：型号、组件
      symptoms: "{vibration_val}"       # 征兆：指标异常、告警码
      objective: "获取故障诊断与维修建议"  # 目标：明确意图
  prompt: "根据以下上下文和知识库信息，给出设备 {$device} 的健康评价..."
```

### 4.2 知识检索输入逻辑

为了提高 RAG（检索增强生成）的准确性，知识检索的输入建议采用「主体+征兆+目标」三段式结构：

1.  **Subject (主体)**: 明确是谁出问题了。如“三级循环水泵 P-204A”、“西门子 PLC S7-1200”。
2.  **Symptoms (征兆)**: 当前具体的异常表现。如“振动幅度超过 7.5mm/s”、“轴承温度持续升高至 95℃”。
3.  **Objective (目标)**: 期望得到的回答类型。如“请对比行业维护标准给出预警等级”或“请提供可能的故障原因排查清单”。

---

## 五、完整字段结构

```yaml
content:
  source:                      # 整表级数据来源（可被 section 级覆盖）
    kind: sql | nl2sql | ai_synthesis
    query: "..."
    description: "..."
  presentation:
    type: composite_table
    columns: 8                 # 总列数
    sections:
      - id: "base_info"        # 建议增加 ID，便于被 ai_synthesis 引用
        band: "区段标题"        # 可选，null 表示无标题行
        layout:
          type: kv_grid | tabular
          # ... layout 专属字段
        source:                # 可选，覆盖整表级 source
          kind: ai_synthesis   # 使用 AI 总结
          # ... ai_synthesis 专属配置
        fields:                # kv_grid 专用
          - key: "..."
            value: "..." | col: "..."
```

---

## 六、约束规则

1. `(key_span + value_span) × cols_per_row` 必须等于 `columns`（kv_grid）
2. `tabular` 中 `headers[].span` 之和必须等于 `columns`
3. `band` 行自动 `colspan=columns`，不需单独声明
4. `kv_grid` 的 `fields` 若数量不能被 `cols_per_row` 整除，最后一行不足的格以空白补齐
5. `tabular` 的 `source` 必填；`kv_grid` 的 `source` 与 `fields.value` 二选其一或混用
6. `ai_synthesis` 引用 `refs` 时，对应的 section 必须在当前 section 之前定义，确保数据已就绪。
