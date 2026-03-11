# 设计评审合并意见 v1

> 来源：`review_by_codex_v1.md` + `review_by_cursor_v1.md`  
> 整理时间：2026-03-11  
> 状态：待处理，**未做任何修改**

---

## 总体评价

两方均认可整体结构分层合理（参数系统 → 章节树 → 内容节点"来源 × 呈现"解耦），具备工程落地基础。主要差距在于：**Codex 侧重 Schema 约束严密性**，**Cursor 侧重运行时行为规范与系统边界声明**。两份意见高度互补。

---

## 合并问题清单

### A. Schema 结构约束不足（Codex 主提）

| # | 问题 | 位置 |
|---|---|---|
| A1 | `content` 与 `subsections` 互斥仅文档声明，Schema 未用 `oneOf` 强制，允许同时出现导致渲染歧义 | `template.schema.json` |
| A2 | `input_type=enum` 时 `options` 未标为必填；`input_type=dynamic` 时 `source` 未标为必填 | `$defs/Parameter` |
| A3 | `source.kind=sql` 时 `query` 未标为必填；`kind=nl2sql` 时 `description` 未标为必填 | `$defs/Source` |
| A4 | `presentation.type` 对应的条件字段（`template`/`anchor`/`chart_type`/`headers`）未用 `if/then` 强制 | `$defs/Presentation` |
| A5 | `foreach.param` 未约束只能绑定 `multi:true` 的参数；未禁止嵌套 `foreach` | `$defs/Foreach` |
| A6 | 保留变量 `{$value}` 未在 Schema/规则中标记，`foreach.as` 若取名 `value` 会冲突 | 占位符规则 |

---

### B. 参数系统能力缺口（两方均提）

| # | 问题 | 来源 |
|---|---|---|
| B1 | 缺少派生/计算参数支持：示例中 `time_range_start` 由 `time_range` 推导，但被标为 `required`，会错误提示用户填写 | Codex |
| B2 | 缺少 `default` 字段及其语义（静态默认值 vs 动态计算） | Cursor |
| B3 | 缺少参数校验规则（正则、数值范围、长度限制） | Cursor |
| B4 | `dynamic` 参数的返回格式未定义（`[{value, label}]` 还是任意结构），不同接口实现会不一致 | Cursor |
| B5 | 枚举参数未支持「自由输入 + 枚举混选」模式（如附加 `allow_free_text`） | Cursor |

---

### C. 运行时行为规范缺失（两方均提）

| # | 问题 | 来源 |
|---|---|---|
| C1 | 多值参数在 `text` 模板和 SQL `IN ({device_ids})` 中的展开规则未定义：引号、分隔符、转义，容易产生 SQL 语法错误或注入风险 | Codex |
| C2 | `foreach` 绑定参数为空数组时的渲染策略未定义（直接跳过 vs 渲染"暂无数据"占位） | Cursor |
| C3 | `foreach.as` 变量的作用域规则未明确（子章节是否可继续引用） | Cursor |
| C4 | `nl2sql` 生成 SQL 失败时的降级策略未定义（整体失败 vs 显示局部占位提示） | Cursor |
| C5 | `chart` / `composite_table` 列映射规则未定义：SQL 结果列如何对应 x/y/series 或合并表头列 | Codex |

---

### D. nl2sql 安全与边界（Codex 主提）

| # | 问题 |
|---|---|
| D1 | 可访问的表/字段白名单未定义，LLM 可能生成越权查询 |
| D2 | 最大结果量、超时限制未定义，存在不可控查询与成本风险 |
| D3 | 审计日志策略未描述 |

---

### E. 模板元信息与选择策略（Cursor 主提）

| # | 问题 |
|---|---|
| E1 | 模板缺少版本号（`version`）、启停标记（`enabled`）等元信息字段 |
| E2 | 同 `type + scene` 下若存在多个版本模板，选取优先级未定义 |
| E3 | 是否由「模板管理系统」负责选取逻辑未在文档中声明边界 |

---

### F. 章节与内容节点能力边界（Cursor 主提）

| # | 问题 |
|---|---|
| F1 | 单章节「图 + 表 + 文字解释」组合场景未覆盖，尚不清楚是拆为多个 `content` 节点还是新增 `composite` 高层类型 |
| F2 | `foreach` 是否允许只包裹 `content`（无子章节），当前示例均为有子章节模式（Codex 也提到此问题） |

---

### G. 系统级关注点（Cursor 主提）

| # | 问题 |
|---|---|
| G1 | 权限与数据隔离边界未声明（总部 vs 分部角色可见字段差异、租户隔离） |
| G2 | 报告导出目标格式未定义（在线查看 / docx / pdf / html），直接影响表格合并单元格能力和图表渲染方式 |
| G3 | 缺少端到端渲染流水线视图（参数收集完成 → sections 遍历 → foreach 展开 → SQL/nl2sql 执行 → 文档拼装 → 出错降级） |
| G4 | 可观测性缺失：每次生成任务缺少 trace id / job id、关键节点结构化日志 |

---

## 优先级建议

| 优先级 | 条目 | 理由 |
|---|---|---|
| P0（阻塞实现） | A1–A6、C1、C5 | Schema 漏洞或运行时行为歧义，不解决会导致渲染层各自约定 |
| P1（影响交互质量） | B1–B4、C2–C4 | 参数派生、空列表、降级策略，直接影响用户体验 |
| P2（完整性补充） | D1–D3、E1–E3、F1–F2、G1–G3 | 安全、元信息、边界声明，可在后续迭代补充 |
| P3（可观测性） | G4 | 不影响功能，但影响运维排查效率 |
