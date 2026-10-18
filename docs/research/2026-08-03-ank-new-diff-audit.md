# ANK `.new` 差异审计

日期：2026-08-03

结论：保留用户已经建立的 Product、Constitution 与文档地图；把 profile 中已确认的
路径、任务同步、红线和验证命令合并到活跃 Claude 入口。`.new` 文件作为 ANK 非覆盖
生成证据暂时保留，不把它们当作运行入口。

| `.new` | 决策 | 理由 |
|---|---|---|
| `.claude/settings.json.new` | adapt | 拒绝自然语言 Bash allow 和残留 lint/test 占位符；活跃 settings 改为 pytest、ruff、compileall |
| `.claude/rules/sop-feature.md.new` | adapt | 采用 Spec、Architecture、文档对齐和审批路径；构建项改为真实 Python 验证命令 |
| `.claude/rules/harness-sop.md.new` | adapt | 合并 skillhub 路径/profile；profile 当前 disabled，factory-check 明确 skip |
| `.claude/rules/task-sync-sop.md.new` | adopt | 合并无凭证 OB/飞书路径、分类、P1 和同步命令 |
| `.claude/rules/rules-six-redlines.md.new` | adapt | 合并 Auto Git 红线，清理重复的“占位符替换”文案 |
| `.claude/commands/factory-check.md.new` | adapt | 拒绝自然语言“构建命令”；使用 48 项测试对应的真实验证入口 |
| `.claude/commands/task-sync.md.new` | adopt | 合并 profile 中的任务同步命令 |
| `docs/README.md.new` | reject | 内容比现有中文文档地图更少，会丢失 PRD、ADR、Handoff 和工作流入口 |
| `docs/constitution.md.new` | reject | 含 `YYYY-MM-DD` 且会覆盖用户已确认的 12 条产品原则 |
| `docs/sync/_ob-task-sync-template.md.new` | reject | 它是一次性具体化结果；现有文件应继续作为可复用模板保留占位字段 |
| `CLAUDE.md.new` | adopt | 仅补充产品一句话说明，不覆盖现有入口 |

## 占位符结论

- 活跃 `.claude/settings.json`、rules 和 commands 已无 `{{...}}` 运行占位符。
- `docs/sync/_ob-task-sync-template.md` 等明确命名为 template 的文件保留模板字段，属于
  设计用途，不是未解释的运行时占位符。
- `docs/constitution.md.new` 中的日期占位符不合并。
- `AGENTS.md` 中“占位符”字样是模板维护说明，不是待替换值。

## 非覆盖边界

没有删除或覆盖用户的 `docs/constitution.md`、`docs/PRODUCT.md`、`docs/README.md`。
没有删除 `.new` 证据文件；若后续要清理，应在确认模板源已修正后单独执行。
