# 设计评审（Codex）v1

> 评审范围：`E:\code\antigravity_projects\ReportTemplate\design.md`、`E:\code\antigravity_projects\ReportTemplate\template.schema.json`、`E:\code\antigravity_projects\ReportTemplate\example_device_health_hq.yaml`

## 总体结论
- 结构清晰、概念分层合理（参数系统、章节树、内容节点的“来源 × 呈现”），具备落地的基础。
- 目前的 Schema 约束与设计文档存在多处“允许无效模板通过”的缺口，建议补充结构约束与运行期校验规则。

## 主要问题与风险
- `content` 与 `subsections` 的互斥只在文档中说明，Schema 未强制。当前会允许“既有内容又有子章节”的模板，渲染逻辑会歧义。
- `foreach` 的使用规则不完整：未限制仅能绑定 `multi: true` 参数、未禁止嵌套 `foreach`、未明确 `foreach` 与 `content` 的搭配规则。
- 条件字段缺少强制：`input_type=enum` 时 `options` 必填、`input_type=dynamic` 时 `source` 必填；`source.kind=sql` 时 `query` 必填、`nl2sql` 时 `description` 必填；`presentation.type` 对应的 `template/anchor/chart_type/headers` 也应强制。
- 多值参数的“字符串展开规则”未定义：在 `text` 模板与 SQL `IN ({device_ids})` 中如何拼接、是否加引号、如何转义都未明确，容易造成 SQL 语法错误或注入风险。
- `nl2sql` 的安全与边界未定义：可访问的表/字段白名单、最大结果量、超时与审计策略未描述，可能带来不可控查询与成本风险。
- 计算型参数未建模：示例中的 `time_range_start` 由系统计算但仍是 `required`，当前 Schema 无法表达“派生参数/依赖关系”，会导致交互流程模糊。
- `chart` 与 `table` 的列映射规则未定义：SQL 结果如何映射到图表的 x/y/series 或复合表头列，需要明确，否则前端渲染不可预测。
- 占位符命名冲突未处理：`{$value}` 作为保留变量未在 Schema/规则中标记，`foreach.as` 若取值为 `value` 可能引发冲突。

## 建议补充的约束/规则
- 在 Schema 中使用 `oneOf/anyOf` 约束 `content` 与 `subsections` 互斥，并加上 `if/then` 的条件必填规则。
- 引入模板静态校验器：检查未定义的 `{param}`、未定义的 `{$var}`、未使用的必填参数、`foreach.param` 是否绑定 `multi:true`。
- 明确多值参数的默认展示格式与 SQL 绑定方式，建议统一为“参数化查询 + 数组绑定”，避免字符串拼接。
- 对 `nl2sql` 增加可访问资源范围（表/字段白名单）与查询限制（行数、耗时），并要求审计日志。
- 为 `chart` 与 `composite_table` 补充列映射声明（如 `x`, `y`, `series`, `columns`），避免仅靠位置推断。
- 为派生参数增加字段（如 `computed: true`、`depends_on` 或 `derive`），避免在交互环节提示用户填写系统计算字段。
- 明确保留关键字列表（如 `value`），禁止 `foreach.as` 与参数 `id` 使用保留名。

## 需要确认的问题
- `foreach` 是否允许只包裹 `content`（无子章节）？当前文档示例为“有子章节”模式。
- `chart_type` 在 `nl2sql` 场景是必填还是可让 LLM 决定？若允许 LLM 决定，是否需要返回图表类型并在模板中覆盖？
- 多值参数（如 `device_ids`）在自然语言段落中是否需要自定义格式化（如仅展示前 N 个 + 其他）？
