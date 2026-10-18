---
title: "Auto Git Constitution"
type: constitution
status: active
created: 2026-08-02
updated: 2026-08-03
tags: [constitution, engineering, ai-native]
related:
  - "[[product/product-definition.md]]"
  - "[[engineering/architecture/auto-git.md]]"
---

# Auto Git 工程宪章

本文件记录 Auto Git 跨版本稳定原则。Agent 规则、Skill、CLI、hooks、CI 模板和版本
计划不得与这些原则冲突。

## 不可妥协原则

1. **使用标准 Git。** 不创造私有仓库格式；所有变更可被普通 Git 工具读取和恢复。
2. **事实先于推断。** 仓库状态、分支、diff、远程和执行结果来自机器可读 Git 输出，
   不从聊天或目录名猜测。
3. **Preview 与 Apply 分离。** 写入型 Git 动作必须引用用户已经看到的同一份未漂移
   计划；状态变化后重新预览。
4. **自动化不取消审批。** Commit、Push、merge、tag、Release 和破坏性恢复根据风险
   分别授权；默认不自动公开发布。
5. **恢复优先。** 不把 `reset --hard`、`clean -fdx`、强推或删除分支当作普通修复；
   破坏性动作必须先备份、解释风险并获得明确批准。
6. **本地门禁与远程 CI 分层。** 回归测试定义检查什么；本地门禁在 Commit/Push 前
   执行，CI 在 Push/PR 后独立复验。两者不能互相冒充。
7. **Skill-first 且运行时低耦合。** Auto Git 是一个独立安装的 Agent Skill。
   Skill Engineering 在开发期创建和治理它，但 Auto Git 运行时不依赖 ANK、
   Skill Engineering、特定 Agent、模型 Provider、GitHub 或云服务。
8. **Skill 与 Scripts 分工。** 根 `SKILL.md` 负责自然语言、教学、策略选择和审批；
   Skill 内 `scripts/` 负责状态、执行、验证、锁和恢复。用户不需要再安装第二个
   Auto Git 产品。
9. **兼容旧项目。** 接入 Auto Git 不得要求项目重写现有 Git 历史、CI 或开发方式；
   默认从只读盘点和最小配置开始。
10. **安全与隐私。** 凭证、Cookie、私钥、完整对话和敏感 diff 不进入仓库或运行
    记录；只保存必要的脱敏事实与指针。
11. **功能先有 Spec 与 Plan。** TDD、回归、失败路径和文档对齐是交付的一部分。
12. **项目账本对齐。** 任务完成前同步 Repo、Agent 状态和 OB/外部任务；同步失败要
    明确报告。

## 角色契约

- 用户：通过 Agent 完成开发和知识工作，希望理解关键 Git 决策，但不必背命令。
- AI：Auto Git 工程副驾，先解释真实影响，再在权限边界内执行。
- 语言：默认简体中文。
- 反馈：先给结果、影响和下一步；命令解释兼顾 Git 训练。

## 记忆边界

- 可进入仓库：`.ai-native/profile.json`、公开产品事实、脱敏测试 fixture 和配置 schema。
- 只留本机：Agent memory、用户级 MCP、Keychain、SSH config 和真实项目路径映射。
- 禁止保存：token、私钥、Cookie、原始敏感对话和不必要的完整 diff。

## 变更协议

修改本宪章必须先写 ADR 和 Spec，说明兼容影响，并同步 Product、Architecture、Agent
入口和测试。普通 Sprint 或聊天决定不能静默覆盖宪章。
