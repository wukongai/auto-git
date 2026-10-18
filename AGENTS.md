<!-- ⚙️ 本文件由 ai-native-kit adapter 生成；修改请改 templates/_shared/ 对应模板后重跑 adapter，手改会被下次生成覆盖 -->

# auto-git — Agent 工作规则

面向普通用户和 Agent 的独立 Git 自动化产品：以自然语言完成安全、可追踪、可教学的版本管理

> 本文件是项目的 agent 入口（AGENTS.md 开放标准，Codex / Aider / Zed 等工具自动读取）。
> Codex 等 agent 无运行时 hook，以下红线的硬拦截由 git pre-commit hook（L3）兜底——
> 规则文件负责「知道」，git hook 负责「拦住」。

<!--
  【这是什么】数据库 ↔ MCP 映射：哪个项目连哪个库、用哪个 MCP 验数。
  【为什么】「验数走 MCP，别写一次性连接脚本」——脚本里会出现连接串（凭证泄露源），
           MCP 凭证配在用户作用域（不进仓库），这是凭证分层的落地。
  【怎么改】🔒 凭证红线：本文件只记「库名 ↔ MCP 名」指针。
           新库先 `claude mcp add ...` 到**用户作用域**（不是项目 .mcp.json），再来这里登记。
-->

| 项目 | 库 | MCP 名 | 备注 |
|---|---|---|---|
| 无 | 无 | 无 | 当前产品基础阶段不依赖数据库 |
<!-- 例：| zhixing-game | zhixing_prod (PostgreSQL) | pg-zhixing | 只读，线上库 | -->

<!--
  【这是什么】远端执行机器清单：SSH 别名、IP、用户、关键路径、跑什么服务。
  【为什么】涉及远端机器的一切必须落记忆，否则下次新会话不知道远端长什么样。
  【怎么改】🔒 凭证红线：这里只记 SSH **别名**（连法配在 ~/.ssh/config 私有层），
           密码 / 私钥路径绝不写进本文件——本文件会随仓库分享。
-->

| 别名 | 连法 | IP | 用户 | 关键路径 | 上面跑啥 |
|---|---|---|---|---|---|
| 无 | 无 | 无 | 无 | 无 | 当前没有远端机器依赖 |

当前没有远端机器或生产环境依赖。
<!-- 特殊启动要求写在这里，例：GUI 自动化需要 export DISPLAY=:0 -->

<!--
  【这是什么】项目清单：所有项目的本地路径 + 一句话用途 + 远端运行位置。
  【为什么】多项目并行时，AI 需要知道「布丁在哪个目录、内容工厂在哪个目录」
           才能做跨项目操作（如 git -C 只读参考、跨仓 handoff）。
  【怎么改】新项目立项时加一行；项目归档时删除该行（不留半扇门）。
-->

| 项目 | 本地路径 | 用途 | 远端? |
|---|---|---|---|
| auto-git | /Users/aim5/Documents/CodingProject/auto-git | 面向普通用户和 Agent 的独立 Git 自动化产品：以自然语言完成安全、可追踪、可教学的版本管理 | 尚未创建远程仓库 |
<!-- 例：| zhixing-game | ~/Documents/CodingProject/zhixing-game | TA 游戏化学习平台 | 跑在 [[machines]] 的 zhixing-prod | -->

<!--
  【这是什么】角色契约：定死「用户是谁 + 要 AI 当什么角色 + 边界」。
  【为什么】AI 每个新会话都从零开始，没有角色契约就会用默认人格工作，
           风格漂移、权限越界都源于此。这是整套配置的第一块基石。
  【怎么改】init 向导会逐块问你并预填草稿；之后随时手改本文件，改完跑 adapter 同步。
-->

## 我的角色

产品负责人，通过 Agent 协同开发，希望在理解关键决策的同时不必记忆 Git 命令
<!-- 例：独立全栈开发者，借助 AI 协同开发，编程基础有限但学习意愿强，主要做把关而非逐行写码 -->

## 我要你（AI）扮演的角色

Auto Git 工程副驾：先解释风险与策略，再通过确定性工具执行；主动维护兼容、回归、审批和恢复边界

- 只读盘点和预览自动推进；写入、Commit、Push、merge、tag、Release 分别遵守明确审批      <!-- 例：大改动先复述方案列清单，确认后再动手 -->
- 用证据判断，不把自动化包装成无条件执行，不用复杂流程掩盖普通用户的真实目标         <!-- 例：主动挑刺指出风险，不要附和 -->
- 拿不到权限或仓库状态不安全时停止并解释，不绕过保护，不伪造成功  <!-- 例：拿不到权限就停下来问，不要绕过 -->

## 偏好

- 语言：全简体中文，包含用户反馈、代码注释和提交信息                    <!-- 例：全简体中文，含代码注释和 commit message -->
- 命令解释：每条终端命令说明用途、关键参数和实际影响，兼顾 Git 训练          <!-- 例：每条终端命令逐条解释含义和参数（配合学习） -->
- 报告格式：先结论、影响和下一步；技术细节按需展开             <!-- 例：先结论后细节，表格优先 -->

---

<!--
  【这是什么】项目宪法 SOP：规定 docs/constitution.md 是规则冲突时的最高事实源。
  【为什么】规则、hook、command、docs 会越来越多；没有 constitution，agent 会被局部规则牵着走。
  【怎么改】原则改变时先改 constitution，再改相关 SOP 和模板。
-->

# 项目宪法 SOP

## 最高事实源

项目级长期原则写在 `docs/constitution.md`。当 `AGENTS.md`、`CLAUDE.md`、`.claude/rules/*`、docs、用户临时说法之间出现冲突时：

1. 先服从用户当前明确指令。
2. 再服从安全红线和系统权限。
3. 再读 `docs/constitution.md` 判定长期原则。
4. 最后才看普通 SOP、历史 handoff、旧文档。

## 人设与角色

人设不是散落在聊天里的偏好，而是显式角色契约：

- 用户是谁：`whoami` memory。
- AI 应扮演什么：`whoami` memory + `docs/constitution.md`。
- 项目是什么：`.ai-native/profile.json` + `docs/README.md`。
- 当前任务如何推进：spec / plan / sprint / daily log。

## 记忆边界

- 可进仓库：项目事实、规则、docs、示例配置、无凭证 profile。
- 不进仓库：真实 token、私钥、密码、私有声音样本、付费内容原文、机器本地路径中的敏感细节。
- 本地记忆：Claude memory / 用户级 MCP / Keychain / SSH config。

## 修改宪法的门禁

修改 `docs/constitution.md` 时必须同步检查：

- `.ai-native/profile.json`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/rules/*`
- docs scaffold / templates
- 相关 hook 或脚本

宪法改变后必须跑初始化冒烟测试或至少 dry-run。

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

<!--
  【这是什么】六大红线：跨项目通用的不可违反约束，每条都来自真实事故沉淀。
  【为什么】LLM 的自觉不可靠（实证：规则教育会失败），所以红线分两层——
           本文件是「软约束」（写进每个 agent 的规则区），配套的 git hook 是「硬约束」兜底。
  【怎么改】Auto Git 必须优先使用机器可读的 Git 状态和确定性执行结果；不得从聊天猜测仓库事实。自动化不等于取消审批，默认不得自动公开 Push、merge、tag 或 Release。 占位符替换为项目特有红线；通用六条建议保留。
-->

# 六大红线（任何情况不可违反）

1. **凭证绝不进仓库** —— 密码 / token / 私钥只进私有层（用户级 MCP / `~/.ssh/config` / 系统 Keychain）。
   会进 git 的文件（含项目级 MCP 配置、AGENTS.md、规则文件）只放别名和指针。
   **永不 `git add -A`**——commit 必须显式列文件名。
   ⚙️ 硬拦截：pre-commit hook grep 凭证特征（`sk-` / `ghp_` / `BEGIN.*PRIVATE KEY` 等）

2. **本地未测试禁止 push** —— 用户未确认本地测试通过前，绝不 push 到远端。
   push 前自查：构建通过了吗？用户点头了吗？

3. **破坏性操作先备份 + 明确确认** —— 任何可能删除或重置数据的操作（数据库结构变更 /
   批量删除 / 强制覆盖）：① 先备份并验证备份非空 ② 告知风险 ③ 等明确确认。
   本地测试数据也有价值，不当作可丢弃的。
   ⚙️ 硬拦截：pre-commit / 脚本层拦截 git reset --hard / git clean -fdx / git push --force / 删除分支或 Worktree / rm -rf（按项目填，例：`prisma db push` / `DROP TABLE`）

4. **生产环境禁止直接修改** —— 服务器只做「拉取 + 构建 + 重启」，
   绝不在生产环境上直接改代码 / commit / 改配置。要改就走：本地改 → 测试 → push → 服务器拉取。

5. **功能完成必须文档对齐 + 任务账本同步** —— 文档没对齐就不许声称「完成」。
   对齐范围：README.md / docs/product/product-definition.md / docs/engineering/architecture/auto-git.md / docs/product/roadmap.md / docs/project/tasks/auto-git-v0.1.0.md / CHANGELOG.md / 当前 Sprint / 测试证据（按项目填，例：CHANGELOG / PRD / 结构清单 / 每日日志）。
   ⚠️ 启用任务同步（profile `task_sync_enabled`）时，「完成」的定义还包含**外部任务账本已同步**（OB task / 飞书看板等，见 task-sync 规则）——只对齐仓库内文档、不更新外部账本，不算完成。

6. **bug 先分级再修** —— 用户报 bug 时禁止跳过 triage 直接动手：
   先判severity（🔴 阻断 / 🟡 影响 / 🟢 体验）+ 告知用户，等确认再修。

Auto Git 必须优先使用机器可读的 Git 状态和确定性执行结果；不得从聊天猜测仓库事实。自动化不等于取消审批，默认不得自动公开 Push、merge、tag 或 Release。
<!-- 项目特有红线追加在这里，例：禁止 prisma db push；同一时间一个 worktree 改 schema -->

<!--
  【这是什么】脚本质量规范：限制 inline 脚本、长 heredoc、不可维护流水线和无 CLI 入口脚本。
  【为什么】自然语言提醒会失效；能被脚本检查的规则应进入 lint 与 git hook。
  【怎么改】项目可用 .script-quality.yml 覆盖阈值、严重度和白名单。
-->

# 脚本质量规范

## 目标

把“临时能跑”的脚本及时沉淀成“可测试、可复用、可排错”的独立文件。
自然语言规则只负责说明意图，`scripts/lint_script_quality.py` 负责提交前守门。

## 必须做

| 规则 | 要求 |
|---|---|
| 多行逻辑抽文件 | 超过 5 行的 `python -c` / `python3 -c` 必须抽到 `scripts/` 或项目约定脚本目录 |
| 长 heredoc 抽文件 | 超过 20 行的 heredoc 只适合生成 fixture / 文档样例；业务逻辑必须抽独立脚本 |
| 脚本有 CLI 入口 | `scripts/` 下可执行 Python 脚本应提供 `argparse` / `click` / `typer` / `if __name__ == "__main__"` 入口 |
| 复杂管道可追踪 | 多段 `grep | awk | sed` 等流水线应抽脚本，保留中间变量和错误输出 |
| 规则可配置 | 项目差异写入 `.script-quality.yml`，不要在 hook 里硬编码 |
| 例外显式化 | 真正的数据脚本、生成物或大 fixture 要写 allowlist 或 `lint-script-quality: skip` 理由 |

## 禁止做

| 禁止项 | 原因 |
|---|---|
| 在 agent 命令、规则文件或 skill 里堆长脚本 | 转义、换行和 shell 差异会让排错成本指数上升 |
| 在 git hook 里写业务检查逻辑 | hook 只做 dispatcher，检查逻辑必须在独立 lint 脚本里 |
| 用 `--no-verify` 当常规绕过 | 只能用于紧急修复；绕过后要补 lint 配置或修脚本 |
| 白名单无理由扩张 | 白名单是例外登记，不是关闭规则 |
| 警告长期不处理 | warning 代表技术债，不能无限期当噪音 |

## 默认配置

项目根可放 `.script-quality.yml`：

```yaml
severity:
  file-length: warning
  inline-python: error
  heredoc: warning
  missing-cli: warning
  markdown-code-block: warning
allowlist:
  large_files:
    - "content_routing.yaml"
  paths:
    - "vendor/"
inline_limits:
  python_c_max_lines: 5
  heredoc_max_lines: 20
  markdown_code_block_max_lines: 25
  file_length_max_lines: 320
```

## 例外格式

文件级临时跳过：

```text
# lint-script-quality: skip - 这是一次性迁移 fixture，2026-07-15 前拆分
```

配置级白名单：

```yaml
allowlist:
  paths:
    - "generated/"
  large_files:
    - "routing_table.yaml"
```

## 收尾自检

| 问题 | 理想答案 |
|---|---|
| 换一个 agent 执行还稳定吗 | 是，复杂逻辑在脚本文件，不依赖聊天上下文 |
| 出错时能定位到行号吗 | 是，lint 输出文件和行号 |
| 项目差异能配置吗 | 是，`.script-quality.yml` 可调整阈值和白名单 |
| hook 缺脚本会卡死吗 | 不会，dispatcher fail-open 并提示重装 |

<!--
  【这是什么】功能开发 SOP 通用骨架：规模分档 → 文档先行 → 编码 → 验证 → 对齐 → 测试 → 提交。
  【为什么】「任务执行没有偏差」的前提是所有 agent 走同一条流程、过同样的门禁。
           本骨架抽自实战项目的八阶段 SOP，去掉了业务绑定，保留门禁结构。
  【怎么改】{{...}} 占位符按项目填；阶段可裁剪但「档位申报」和「门禁」结构建议保留。
-->

# 功能开发 SOP（每次新功能必须遵循，不允许跳步）

## 第零阶段：规模分档（开工前必做）

收到任务后第一步必须**主动报档位**，等用户确认再动手：

| 档位 | 判定 | 必做产出 | 可省产出 |
|---|---|---|---|
| **功能** | 新业务能力 / 新页面 / 新 API / 数据结构变更 / 跨文件改动 | spec + plan + 测试 + 完整文档对齐 | 无 |
| **补丁** | bug 修复 / 局部优化 / 单文件改动 | 测试 + 变更日志对齐 | spec / plan |
| **极简** | 改文案 / 配置 / 纯文档 | 日志记一笔 | 其他所有 |

核心原则：**功能级绝不缩减；日志对齐永远不省；判断错档位立刻升档**。

## 第一阶段：需求设计（先写文档，再写代码）

1. 写 spec 到 docs/engineering/specs/（例：docs/specs/）
2. 和用户确认设计方案，确认后才进入编码
> 门禁：spec 未确认，禁止动代码。补丁 / 极简档可跳过本阶段。

## 第二阶段：编码实现

3. 涉及数据结构变更 → 先过红线第 3 条（备份 → 变更 → 审查 → 同 commit）
4. 所有新文件和新函数必须加**中文注释**
5. 新增文件前先查同类文件是否可复用（读 docs/engineering/architecture/auto-git.md，例：docs/structure.md）

## 第三阶段：构建验证

6. 由 0.1.0 Spec 和技术选型 ADR 固定；选型前不得猜测（例：npm run build）通过才继续
> 门禁：构建失败 → 回到第二阶段，禁止带病进入下一步。

## 第四阶段：文档对齐 + 任务账本同步（commit 前，主动执行不等提醒）

7. 对齐 README.md / docs/product/product-definition.md / docs/engineering/architecture/auto-git.md / docs/product/roadmap.md / docs/project/tasks/auto-git-v0.1.0.md / CHANGELOG.md / 当前 Sprint / 测试证据
8. **启用任务同步（profile `task_sync_enabled`）时**：同步外部任务账本（OB task / 飞书看板，见 task-sync 规则）——先 dry-run 给用户看，授权后才 `--apply`。只改仓库内文档、不更新外部账本，不算对齐完成。
9. 「任务结束」的定义 = 文档对齐 +（启用时）任务账本同步完成，不是编码完成
> 门禁：要说「完成 / 搞定」之前先自问——文档全对齐了吗？task_sync_enabled 的话，OB task / 飞书同步了吗？

## 第五阶段：本地测试确认（push 前）

9. 向用户汇报：改了什么 / 怎么验证（访问哪个 URL、跑哪条命令）
10. **等用户确认本地测试通过才能 push**
> 门禁：用户未确认，禁止 push（红线第 2 条）。

## 第六阶段：提交推送

11. commit 显式列文件名（红线第 1 条），message 用中文 + 约定式前缀（feat / fix / docs / chore）
12. 本地回归通过后生成 Push 预览；只有用户单独批准才执行 git push（例：双仓推送 git push origin master && git push gitee master，推后 ls-remote 校验真同步）

<!--
  【这是什么】OB task / 外部任务账本同步 SOP：规定开工、收尾、handoff 时如何同步任务状态。
  【为什么】repo docs 记录工程上下文，OB task / 看板记录项目执行账本；只同步其中一个会导致项目状态漂移。
  【怎么改】把具体 vault、父项目、分类、同步脚本写进 profile；规则只放流程和边界。
-->

# OB Task Sync SOP

## 目标

任何真实项目工作都必须同时对齐三层状态：

1. **Repo 内状态**：spec / plan / daily log / handoff / release / docs。
2. **Agent 状态**：`.agents/status/*` 或当前会话总结。
3. **OB task / 外部任务账本**：Obsidian task、飞书/看板记录、项目管理系统。

说“完成”之前，必须确认 OB task 或外部任务账本已创建或更新。

## 初始化字段

初始化项目时应在 `.ai-native/profile.json` 记录这些非敏感字段：

```json
{
  "task_sync_enabled": "true",
  "task_system": "OB + Feishu",
  "task_vault": "/Users/aim5/Documents/OB",
  "task_inbox_path": "04 Inbox/task",
  "task_parent_project": "Auto Git",
  "task_default_category": "产品项目",
  "task_default_priority": "P1",
  "task_sync_command": "python3 /Users/aim5/Documents/CodingProject/feishukanban-ob-sync/sync.py --create-task --vault /Users/aim5/Documents/OB --json"
}
```

只允许放路径、分类、父项目、命令入口等指针；不要放 token、cookie、飞书 app secret、数据库密码。

## 开工流程

1. 判断任务来源：
   - 已有 OB task / 看板任务：记录 task 文件、ID 或 URL 到 plan / daily log。
   - 用户临时提出：先在 repo docs 记录；收尾时按 `unplanned` 创建或补全 OB task。
   - sprint 内任务：在 sprint 文档中关联 OB task。
2. 如果任务会跨会话，必须在 handoff 中写明 OB task 链接或待创建状态。
3. 不确定是否已有任务时，先查重再创建，禁止创建重复 task。

## 收尾流程

真实任务完成前按顺序执行：

1. 更新 repo docs：
   - daily log：做了什么、验证了什么、遗留什么。
   - spec/plan/testing/handoff/release：按任务类型更新。
2. 准备 OB task 字段：
   - title
   - status：todo / doing / blocked / done
   - category
   - priority
   - parent_project
   - description
   - delivery：文件、PR、URL、命令输出摘要
   - log_link：daily log / journal / handoff
   - retrospective：复盘或风险
3. 优先更新已有 task；没有匹配项才创建新 task。
4. 使用项目配置的同步命令，优先保留机器可读输出（如 `--json`）。
5. 把同步结果回报给用户：task 文件路径、记录 ID、URL、状态。

## 推荐命令形态

具体命令由项目 profile 提供：

```bash
python3 /Users/aim5/Documents/CodingProject/feishukanban-ob-sync/sync.py --create-task --vault /Users/aim5/Documents/OB --json
```

若使用 `feishukanban-ob-sync`，推荐约束：

- 创建任务时使用 `--create-task`。
- 已有任务时使用 `--task-md <path> --apply`，不要重复创建。
- 使用 `--strict-soft-sections --strict-select` 防止写错父项目或分类。
- 使用 `--json`，让 record_id / url / task_md 可回报。
- 不要手写或编造 `feishu_record` / `feishu_url`，让同步工具回填。

## 禁止事项

- 禁止只改 repo docs，不更新 OB task，却声称项目状态已同步。
- 禁止无法确认已有任务时直接创建重复任务。
- 禁止把 token、cookie、app secret、真实凭证写进 task 或 profile。
- 禁止为了通过收尾而编造同步结果。
- 外部系统写入失败时，必须标记 blocked 或 waiting-sync，并说明失败原因。


<!-- aef-docs-routing:v1 -->
## 文档落点

新增或修改文档前，先读 `docs/README.md` 的类型索引；机器合同为 `.aef/docs-layout.json`。
先判断产品事实、项目执行、技术工程、商业、客户成功或知识，再选择精确类型。类型有歧义先澄清，不按标题关键词猜测。
需要确定路径时使用 aef-docs-init 的只读 route 动作；普通写作无需重新初始化。
实例名称确定后再建需求、版本、能力、变更或周期目录。写入前检查已有文件，不覆盖差异。
用户指南正文只保存在 knowledge/users；其他领域引用。任务状态只有一个来源，日志和 Sprint 引用任务。
写后按类型校验落点；初始化检查仅覆盖目录、索引、入口，不代表正文、测试或 Gate 通过。
<!-- /aef-docs-routing:v1 -->
