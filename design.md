# 智能报告模板系统 — 设计文档

> 版本：v1.0 | 日期：2026-03-10

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
  ├── foreach      可选，循环展开声明
  ├── content      可选，当前节点的内容（叶节点）
  └── subsections  可选，子章节（中间节点）
```

> 一个节点 `content` 与 `subsections` 互斥：有子章节则不直接挂内容。

### 4.2 参数驱动的章节循环（foreach）

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

---

## 五、内容节点类型系统

内容节点（`content`）将**数据来源**与**呈现形式**分离为两个独立维度。

### 5.1 两个维度

#### `source`（数据来源）
| `kind` | 说明 |
|---|---|
| `sql` | 直接执行预定义 SQL，参数作为条件或列 |
| `nl2sql` | 自然语言描述 → LLM 生成 SQL → 执行 |
| 无 source | 纯静态内容，`type: text` 时使用 |

#### `presentation`（呈现形式）
| `type` | 说明 |
|---|---|
| `text` | 纯静态段落，参数占位符直接替换 |
| `value` | SQL 返回单一值，嵌入锚点文本的 `{$value}` 位置 |
| `chart` | 可视化图形，`chart_type` 指定图形类型 |
| `simple_table` | 普通二维表格 |
| `composite_table` | 合并表头的复杂表格，需声明 `headers` 二维数组 |

### 5.2 合法组合矩阵

| source.kind | presentation.type | 备注 |
|---|---|---|
| 无 | `text` | 纯静态文本 |
| `sql` | `value` | 单值填入锚点 |
| `sql` | `simple_table` | 标准结果集表格 |
| `sql` | `composite_table` | 合并表头，列结构已知 |
| `sql` | `chart` | 已知维度统计图 |
| `nl2sql` | `chart` | LLM 推断图类型 |
| `nl2sql` | `simple_table` | LLM 查询结果表 |

> `composite_table` 仅支持 `sql` 来源，因复杂表头需固定列映射，LLM 生成列不可控。

---

## 六、占位符约定

| 语法 | 含义 |
|---|---|
| `{param_id}` | 引用全局参数值 |
| `{$varname}` | 引用 `foreach` 迭代变量当前值 |
| `{$value}` | `presentation: value` 中引用 SQL 返回的单值 |

---

## 七、Schema 与示例

- JSON Schema：见 [`template.schema.json`](./template.schema.json)
- 完整示例模板：见 [`example_device_health_hq.yaml`](./example_device_health_hq.yaml)
