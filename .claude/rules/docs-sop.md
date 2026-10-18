---
name: docs-sop
description: 文档工作台 SOP——dailylog / sprint / superpowers / ADR 的统一写入规则
metadata:
  type: rule
---

<!-- ⚙️ 本文件由 ai-native-kit adapter 生成；修改请改 templates/_shared/ 对应模板后重跑 adapter，手改会被下次生成覆盖 -->

<!--
  【这是什么】docs/ 文档工作台 SOP：规定哪些工作必须写 dailylog、sprint、spec、plan、handoff、ADR。
  【为什么】AI 协作最容易丢的是过程上下文；文档工作台让多 session、多 agent、多人协作可恢复。
  【怎么改】路径可通过 profile 占位符调整；如果项目已有目录，保持兼容但不要删除旧资料。
-->

# 文档工作台 SOP

## 标准目录

| 路径 | 作用 | 触发条件 |
|---|---|---|
| `docs/constitution.md` | 项目宪法、不可变原则、角色与记忆边界 | 初始化项目 / 修改原则 / 规则冲突 |
| `docs/project/logs/` | 兼容旧路径的每日执行记录 | 任何有实际改动或关键判断的工作日 |
| `docs/project/logs/` | 标准每日执行记录、验证结果、遗留问题 | 任何有实际改动或关键判断的工作日 |
| `docs/project/logs/` | 周报、周期复盘、运维摘要 | 每周回顾 / 长周期项目 |
| `docs/project/sprints/` | 阶段目标、范围、验收、复盘 | 多日推进 / 多 agent 并行 / 目标需要拆期 |
| `docs/engineering/specs/` | 功能设计与验收契约 | 新功能 / 新流程 / 架构或数据结构变化 |
| `docs/engineering/changes/` | 实施计划、风险、测试方案 | 功能级工作开工前 |
| `docs/engineering/changes/` | UI / 交互 / 产品方案候选 | 涉及页面、流程、用户体验 |
| `docs/engineering/changes/` | 测试用例、验收记录、回归清单 | 功能级 / 高风险 / 回归敏感工作 |
| `docs/project/handoffs/` | 跨会话交接、恢复现场 | 暂停、换 agent、任务未完成、上下文将丢失 |
| `docs/product/research/` | 功能级 mockup / 原型 | 设计评审、方案比较 |
| `docs/product/research/` | 结构化发散与候选方案 | 需求模糊、方案未定 |
| `docs/engineering/adr/` | 架构决策记录 | 不可逆 / 高成本 / 后续会反复追问的技术选择 |
| `docs/project/tasks/` | 未排期想法与候选任务 | 暂不进入当前 sprint |
| `docs/product/research/` | 调研、对比、评估证据 | 选型、竞品、模型、供应商、方案比较 |
| `docs/knowledge/team/explanations/` | 可重复操作手册 | 需要人或 agent 反复执行的流程 |
| `docs/knowledge/users/guides/` | 教程与学习路径 | 需要教会人或 agent 从零执行 |
| `docs/engineering/` | 工程架构、运行时、harness、工具链事实 | 长期技术事实或工程约束 |
| `docs/engineering/maintenance/runbooks/` | 操作手册、应急流程、回滚路径 | 高频或高风险操作 |
| `docs/engineering/maintenance/environment/` | 新机器、新成员、新 agent 接入 | 环境初始化 / 私有凭证指针 |
| `docs/product/releases/` | 发版记录、验证证据、回滚说明 | 版本发布 |
| `docs/knowledge/references/` | PDF、截图、外部材料、证据附件 | 需要留存原始材料 |
| `docs/product/research/` | 全局 mockup / 原型 | 跨功能视觉产物 |
| `docs/engineering/maintenance/migrations/` | 迁移审计、兼容、回滚 | 数据 / 内容 / 仓库 / 架构迁移 |

## 写入门禁

1. **规则冲突**：先读 `docs/constitution.md`，宪法优先于普通 SOP；若宪法过期，先更新宪法和相关 SOP。
2. **功能级工作**：先有 `spec` 或更新现有 `spec`，再写 `plan`，确认后编码。
3. **UI/交互工作**：必须更新 `designs/` 或 `mockups/`，至少保留方案选择理由。
4. **补丁级工作**：可不写 spec/plan，但必须在 `logs/daily/` 或兼容的 `dailylog/` 记一笔，说明原因、改动和验证。
5. **多日工作**：必须有 `sprints/` 文档承载目标、范围、验收和复盘。
6. **暂停或换手**：必须写 `handoff`，包含当前状态、关键文件、验证结果、风险和下一步。
7. **重大选择**：必须写 ADR，记录背景、决策、后果和备选方案。
8. **发版/部署**：必须写 `releases/` 或更新 playbook 中的验证证据。
9. **任务完成**：说“完成”前必须确认相关 docs 已对齐；启用任务同步（`task_sync_enabled`）时，还必须确认**外部任务账本（OB task / 飞书看板）已同步**（见 task-sync 规则），只对齐仓库内文档不算完成。

## 命名规范

- dailylog：`YYYY-MM-DD.md`
- sprint：`YYYY-MM-DD-sprint-<slug>.md`
- spec：`YYYY-MM-DD-<slug>-spec.md`
- plan：`YYYY-MM-DD-<slug>-plan.md`
- design：`YYYY-MM-DD-<slug>-design.md`
- testing：`YYYY-MM-DD-<slug>-test-plan.md`
- handoff：`YYYY-MM-DD-<slug>-handoff.md`
- ADR：`YYYY-MM-DD-<slug>.md`
- release：`<version>.md` 或 `YYYY-MM-DD-<version>.md`

## 工作顺序

1. 开工前判断档位：功能 / 补丁 / 极简。
2. 功能级：读相关 `docs/engineering/specs/`、`plans/`、`handoff/`。
3. 编码前：必要时新增或更新 spec/plan。
4. 编码后：运行验证命令，记录结果。
5. 收尾前：更新 daily log；未完则补 handoff；跨期则更新 sprint；发版则更新 release。
