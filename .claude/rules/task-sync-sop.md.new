---
name: task-sync-sop
description: OB Task Sync SOP——项目任务、OB task、外部看板/飞书同步的开工与收尾流程
metadata:
  type: rule
---

<!-- ⚙️ 本文件由 ai-native-kit adapter 生成；修改请改 templates/_shared/ 对应模板后重跑 adapter，手改会被下次生成覆盖 -->

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
