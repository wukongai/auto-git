---
name: rules-six-redlines
description: 六大红线——任何 agent 任何情况不可违反的硬约束（从实战事故沉淀的通用不变量）
metadata:
  type: rule
---

<!-- ⚙️ 本文件由 ai-native-kit adapter 生成；修改请改 templates/_shared/ 对应模板后重跑 adapter，手改会被下次生成覆盖 -->

<!--
  【这是什么】六大红线：跨项目通用的不可违反约束，每条都来自真实事故沉淀。
  【为什么】LLM 的自觉不可靠（实证：规则教育会失败），所以红线分两层——
           本文件是「软约束」（写进每个 agent 的规则区），配套的 git hook 是「硬约束」兜底。
  【怎么改】项目特有红线追加在本文底部；通用六条保留。
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
   ⚙️ 硬拦截：pre-commit / 脚本层拦截 `git reset --hard` / `git clean -fdx` /
   `git push --force` / 删除分支或 Worktree / `rm -rf`

4. **生产环境禁止直接修改** —— 服务器只做「拉取 + 构建 + 重启」，
   绝不在生产环境上直接改代码 / commit / 改配置。要改就走：本地改 → 测试 → push → 服务器拉取。

5. **功能完成必须文档对齐 + 任务账本同步** —— 文档没对齐就不许声称「完成」。
   对齐范围：README.md / docs/product/product-definition.md / docs/engineering/architecture/auto-git.md / docs/product/roadmap.md /
   docs/project/tasks/auto-git-v0.1.0.md / CHANGELOG.md / 当前 Sprint / 测试证据。
   ⚠️ 启用任务同步（profile `task_sync_enabled`）时，「完成」的定义还包含**外部任务账本已同步**（OB task / 飞书看板等，见 task-sync 规则）——只对齐仓库内文档、不更新外部账本，不算完成。

6. **bug 先分级再修** —— 用户报 bug 时禁止跳过 triage 直接动手：
   先判severity（🔴 阻断 / 🟡 影响 / 🟢 体验）+ 告知用户，等确认再修。

Auto Git 必须优先使用机器可读的 Git 状态和确定性执行结果；不得从聊天猜测仓库事实。
自动化不等于取消审批，默认不得自动公开 Push、merge、tag 或 Release。
<!-- 项目特有红线追加在这里，例：禁止 prisma db push；同一时间一个 worktree 改 schema -->
