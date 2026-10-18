---
name: harness-sop
description: Agent harness SOP——规则、记忆、commands、hooks、permissions 的能力分层与降级策略
metadata:
  type: rule
---

<!-- ⚙️ 本文件由 ai-native-kit adapter 生成；修改请改 templates/_shared/ 对应模板后重跑 adapter，手改会被下次生成覆盖 -->

<!--
  【这是什么】Agent harness SOP：把 Claude Code / Codex / 其他 agent 的能力差异说清楚。
  【为什么】不能因为 Claude 有 hooks/commands/subagents，就假设所有 agent 都能硬拦截。
  【怎么改】新增 agent adapter 时，先补能力矩阵，再补降级策略。
-->

# Agent Harness SOP

## 能力分层

| 层级 | 作用 | Claude Code | Codex / AGENTS.md 类 agent | 跨 agent 兜底 |
|---|---|---|---|---|
| Rules | 自然语言工程规范 | `CLAUDE.md` + `.claude/rules/*` | `AGENTS.md` 内联 | 共享模板 |
| Memory | 人设、项目事实、机器/数据库指针 | `~/.claude/projects/.../memory/` | 内联到 `AGENTS.md` | `.ai-native/profile.json` + docs |
| Commands | 高频动作入口 | `.claude/commands/*` | 显式脚本 / 文档命令 | `scripts/*` |
| Hooks | 运行时拦截 | `.claude/hooks/*` + settings | 无原生等价 | git hook / factory-check |
| Permissions | allow/deny / sandbox | `.claude/settings.json` | Codex sandbox / approval | 最小权限 + 用户确认 |
| Agents | 子 agent / 专家角色 | `.claude/agents/*` | 只能读说明后由主会话执行 | 角色模板 + docs |
| Skills | 可复用能力包 | `.claude/skills/*/SKILL.md` | `.agents/skills/*/SKILL.md` 或显式项目 `skills/*` | `agent-skill-hub diff` / 项目 README 对账 |

## 设计原则

1. **共享核心优先**：规则、人设、SOP 先进入模板和 docs，再由 adapter 生成运行时文件。
2. **Claude 增强，不绑死**：Claude hooks/commands/agents 是增强层，不是唯一执行路径。
3. **Codex 降级明确**：Codex 不执行 Claude hooks，必须靠 `AGENTS.md` + 脚本 + git hook。
4. **Command 薄壳**：slash command 只做入口和 checklist，复杂逻辑放脚本。
5. **Hook 可测试**：每个阻断型 hook 都应有应拦截/应放行样例。
6. **权限不写凭证**：settings / MCP / commands 只能写命令和别名，不能写 secret。
7. **Skill 入口必须对账**：项目内 `skills/*` 只是源码位置；Claude/Codex 是否能发现，要以 `.claude/skills`、`.agents/skills` 或 skillhub profile 对账结果为准。

## 初始化产物

当启用标准 harness 时，应创建或预览：

- `.claude/settings.json`
- `.claude/agents/doc-sync.md`
- `.claude/agents/pm.md`
- `.claude/agents/tester.md`
- `.claude/agents/reviewer.md`
- `.claude/commands/factory-check.md`
- `.claude/commands/handoff.md`
- `.claude/commands/memory-backup.md`
- `.claude/hooks/protect-env.sh`
- `.claude/hooks/protect-dangerous-rm.py`

默认 settings 只注册 `protect-env.sh` 与 `protect-dangerous-rm.py` 两条底线 hook。
`session-start.sh`、`pre-commit-check.sh`、`prevent-bash-compound.py`、`auto-approve-project-scripts.py`
可作为可选增强文件存在，但不默认挂载，避免 Claude Code 启动、Bash 执行和权限申请被过度干预。

已有文件内容不同必须写 `.new`，禁止静默覆盖。

## Skill 分发检查

如果项目依赖 `agent-skill-hub` 分发 skill，profile 应声明：

- `skillhub_enabled`
- `skillhub_root`
- `skillhub_profile`

收尾或 factory-check 时必须运行：

```bash
PROJECT_ROOT="$(pwd)"
cd "/Users/aim5/Documents/CodingProject/agent-skill-hub" && PYTHONPATH=src python3 -m skillhub.cli diff --profile "auto-git" --project "$PROJECT_ROOT"
```

`diff` 出现 missing / extra 时不能把 skill 配置视为完成。`doctor` 只能证明已有链接未断，不能单独证明 profile 已安装完整。
