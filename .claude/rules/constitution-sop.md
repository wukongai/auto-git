---
name: constitution-sop
description: 项目宪法 SOP——最高原则、角色契约、记忆边界、规则冲突处理
metadata:
  type: rule
---

<!-- ⚙️ 本文件由 ai-native-kit adapter 生成；修改请改 templates/_shared/ 对应模板后重跑 adapter，手改会被下次生成覆盖 -->

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
