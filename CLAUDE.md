<!-- ⚙️ 本文件由 ai-native-kit adapter 生成；修改请改 templates/_shared/ 对应模板后重跑 adapter，手改会被下次生成覆盖 -->

# auto-git

面向普通用户和 Agent 的独立 Git 自动化产品：以自然语言完成安全、可追踪、可教学的
版本管理。

## Claude Code 轻量入口

- 共享规则的完整内容在 `AGENTS.md`；Claude Code 当前入口只保留轻量提示。
- 详细规则在 `.claude/rules/`，按任务关键词主动读取，避免每次会话自动加载整套 SOP。
- 修改规则请改 ai-native-kit 的 `templates/_shared/` 后重跑 adapter。

## 按需规则索引

- `.claude/rules/constitution-sop.md` — 项目宪法 SOP——最高原则、角色契约、记忆边界、规则冲突处理
- `.claude/rules/docs-sop.md` — 文档工作台 SOP——dailylog / sprint / superpowers / ADR 的统一写入规则
- `.claude/rules/harness-sop.md` — Agent harness SOP——规则、记忆、commands、hooks、permissions 的能力分层与降级策略
- `.claude/rules/rules-six-redlines.md` — 六大红线——任何 agent 任何情况不可违反的硬约束（从实战事故沉淀的通用不变量）
- `.claude/rules/script-quality.md` — 脚本质量规范——把复杂脚本抽成独立文件，并用 lint + git hook 形成机器门禁
- `.claude/rules/sop-feature.md` — 功能开发 SOP——规模分档 + 阶段门禁的通用骨架，每次新功能必须遵循不允许跳步
- `.claude/rules/task-sync-sop.md` — OB Task Sync SOP——项目任务、OB task、外部看板/飞书同步的开工与收尾流程


<!-- aef-docs-routing:v1 -->
## 文档落点

新增或修改文档前，先读 `docs/README.md` 的类型索引；机器合同为 `.aef/docs-layout.json`。
先判断产品事实、项目执行、技术工程、商业、客户成功或知识，再选择精确类型。类型有歧义先澄清，不按标题关键词猜测。
需要确定路径时使用 aef-docs-init 的只读 route 动作；普通写作无需重新初始化。
实例名称确定后再建需求、版本、能力、变更或周期目录。写入前检查已有文件，不覆盖差异。
用户指南正文只保存在 knowledge/users；其他领域引用。任务状态只有一个来源，日志和 Sprint 引用任务。
写后按类型校验落点；初始化检查仅覆盖目录、索引、入口，不代表正文、测试或 Gate 通过。
<!-- /aef-docs-routing:v1 -->
