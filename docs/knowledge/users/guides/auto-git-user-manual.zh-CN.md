---
title: "Auto Git 用户手册：从第一次检查到安全发布"
type: tutorial
status: release-candidate
created: 2026-08-03
updated: 2026-08-03
tags: [auto-git, git, agent-skill, tutorial]
related:
  - "[[../../README.md]]"
---

# Auto Git 用户手册

这是一份面向普通用户的操作 Playbook。你不需要先学习 Git 命令，也不需要阅读项目
源码。每一节都会告诉你：

- 可以直接对 Agent 说什么；
- Auto Git 会检查和执行什么；
- 哪一步需要你确认；
- 预期结果是什么；
- 遇到问题时怎样保留现场并继续。

当前版本是 **0.1.0-dev.1 安全修复候选**。GitHub已有备份记录；安全修复需按维护记录
确认应用，真实双远程、正式发行和跨宿主安装仍待验收。

## 1. Auto Git 是什么

Auto Git 是安装在 Codex、Claude Code 等 Agent 宿主中的 Skill。它把你的自然语言
转换成可预览、可验证、可恢复的标准 Git 操作。

你可以说：

> 帮我用 Auto Git 检查这个项目，只读查看，不要修改。

Auto Git 会读取真实的电脑和仓库状态，不从聊天猜分支、改动或远程结果。

Auto Git 不会：

- 在后台一直监控文件夹；
- 因为文件发生变化就自动 Commit 或 Push；
- 把所有文件一次性加入 Commit；
- 未经确认创建远程仓库、Tag 或 Release；
- 保存 Token、密码、Cookie 或私钥；
- 用 force push、`reset --hard` 或批量删除来“修好”问题。

### 预期结果

Agent 能识别 Auto Git，并说明当前动作是只读检查还是需要审批的写入动作。

### 遇到问题

如果 Agent 没有识别 Auto Git，让它检查 Skill 安装范围和宿主发现状态，不要直接执行
写入型 Git 命令。

## 2. 准备一个支持 Skill 的 Agent

Auto Git 需要一个能够读取项目文件、运行本机命令并加载 Agent Skills 的宿主。

当前主要支持：

- Codex；
- Claude Code；
- 基于 Claude Code 的 WorkBuddy。

你还需要一个能运行 `npx` 的 Node.js 环境和系统 Git。当前标准仓库型 Skills CLI
会通过 Git clone 获取 Auto Git，因此 Git 是 Auto Git 首装的前置条件。

可以说：

> 帮我检查当前 Agent 是否支持标准 Agent Skills，以及本机能否运行 npx。只读检查。

### 预期结果

Agent 告诉你宿主名称、Skill 作用范围和 `npx` 是否可用。

### 遇到问题

如果没有 Node.js 或 `npx`，让 Agent使用 Node.js 官方安装方式准备环境，涉及管理员
权限时先解释并等待确认。

### 2.1 完全没有 Git 时

Auto Git 还没有安装，不能先运行自己的 doctor。第一次请直接对当前宿主 Agent 说：

> 我的电脑没有 Git。请检查操作系统，并通过系统官方或受信任包管理器指导安装 Git。
> 先展示命令、来源、管理员权限和影响；我确认后再安装，最后运行 git --version 验证。
> 不要初始化项目、Commit 或 Push。

正确顺序是：

1. 宿主 Agent 只读确认操作系统、架构、包管理器和 `git --version`；
2. 用户确认系统安装计划；
3. 通过操作系统官方入口或受信任包管理器安装 Git；
4. 验证 Git 版本和 PATH；
5. 再按下一节用标准 Skills CLI 安装 Auto Git；
6. Auto Git 安装后重新运行自己的 doctor，继续检查 Python、GitHub CLI 和项目状态。

这不是绕开 Auto Git，而是解决“Skill 还没安装就不能执行 Skill”的自举边界。Auto Git
不会提供另一套私有安装器来掩盖它。

## 3. 安装 Auto Git

> **当前状态：** GitHub已有备份记录；安全修复候选尚未推送，安装试用仍待验收。
> 本轮未核验安装源实时状态。提示仓库不存在时先核对来源与权限，不改用同名仓库。

### 安装到当前项目

```bash
npx skills add wukongai/auto-git
```

这条命令：

- 使用标准 Skills CLI；
- 从 `https://github.com/wukongai/auto-git` 获取 Auto Git；
- 默认只对当前项目生效；
- 不安装独立 Auto Git CLI，也不安装 Skill Engineering。

你可以直接说：

> 帮我从 https://github.com/wukongai/auto-git 安装 Auto Git Skill，只安装到当前项目。
> 安装后检查宿主能否发现它。

### 安装到所有项目

```bash
npx skills add wukongai/auto-git -g -a codex -a claude-code
```

参数含义：

- `-g`：安装到当前用户范围；
- `-a codex`：给 Codex 使用；
- `-a claude-code`：给 Claude Code 使用。

Global 安装会影响多个项目，因此先说清范围：

> 帮我全局安装 Auto Git，让 Codex 和 Claude Code 都能发现。先预览安装范围和目标
> 路径，我确认后再安装。

### Gitee 镜像

Auto Git 会同步到 Gitee 镜像。正式镜像 URL 只有在首次建库、Push 和远端 OID 验证
完成后才会写入手册；不要从未经确认的同名 Gitee 仓库安装。

### 预期结果

- 标准安装器报告 `auto-git` 已安装；
- 当前 Agent 能发现 Skill；
- Agent 能读取 `SKILL.md` 和版本；
- 运行首次 doctor 时能找到 Skill 内 scripts。

### 遇到问题

如果只有文件存在但 Agent 无法触发，不能算安装成功。让 Agent 检查 Codex 的
`.agents/skills` 或 Claude Code 的 `.claude/skills` 发现路径和安装范围。

## 4. 第一次运行

安装后发送：

> 帮我用 Auto Git 检查当前项目。只读运行 doctor 和 inspect，告诉我环境、分支、
> 改动、远程和下一步，不要修改。

Auto Git 会分层报告：

1. Skill 是否就绪；
2. Python 是否满足 scripts 要求；
3. Git 是否安装；
4. GitHub CLI 是否安装和登录；
5. 当前目录是否是 Git 仓库；
6. 当前分支、工作区、暂存区和 Remote；
7. 推荐下一步。

### 预期结果

你能看到机器事实和仓库事实，而不是只有一句“Git 正常”。

### 遇到问题

把完整错误原样交给 Agent：

> 请根据 Auto Git doctor 的错误做诊断。先区分 Skill、Python、Git、PATH、认证和
> Remote 哪一层失败，不要删除配置或注销账号。

## 5. 安装或检查 Git

如果 doctor 发现没有 Git，可以说：

> 帮我生成当前系统的 Git 安装计划。说明官方来源、是否需要管理员权限、会修改什么，
> 我确认后再执行，安装后重新运行 doctor。

Auto Git 会根据系统选择受支持方式：

- macOS：Xcode Command Line Tools、Git 官方入口，已有 Homebrew 时可选择 brew；
- Windows：Git for Windows，已有 WinGet 时可选择精确包；
- Debian/Ubuntu：发行版 apt 包；
- Fedora/RHEL：发行版 dnf 包；
- 未识别平台：只提供官方入口，不拼接未知安装命令。

Auto Git 不会读取或代填系统密码。

### 预期结果

新进程中 `git --version` 可用，PATH 指向预期 Git，doctor 不再报告 Git 缺失。

### 遇到问题

如果安装完成但当前终端仍找不到 Git，先重新打开终端或 Agent，再运行 doctor；不要
重复安装多个来源的 Git。

## 6. 配置提交姓名和邮箱

Git Commit 需要姓名和邮箱。Auto Git 会区分：

- `local`：只影响当前仓库；
- `global`：影响当前用户的所有仓库。

可以说：

> 帮我检查当前项目的 Git 提交姓名、邮箱和配置来源。如果缺失，先让我选择 local
> 或 global，再给我看配置计划。

如果工作与个人项目需要不同身份，优先选择 `local`。

### 预期结果

doctor 能读取有效姓名、脱敏邮箱、配置来源和作用域；Commit 不再因身份缺失被阻断。

### 遇到问题

不要让 Agent 根据 GitHub 昵称自动写入身份。姓名和邮箱必须由你确认。

## 7. 初始化或检查项目

### 新文件夹

> 帮我检查这个文件夹是否已经是 Git 仓库。如果不是，给我看 init 计划，默认分支使用
> main；我确认后再初始化。

### 已有项目

> 帮我 inspect 当前项目，告诉我分支、未提交改动、暂存区、Remote 和 ahead/behind。
> 只读检查。

Auto Git 不会重写已有历史，也不会因为是主分支就自动创建 Worktree。它会根据脏状态、
任务风险和并行工作推荐当前分支、功能分支或 Worktree。

### 预期结果

新目录出现标准 `.git` 仓库；已有项目保持原历史、分支、hooks 和测试方式。

### 遇到问题

如果存在 merge/rebase、detached HEAD 或未知脏改动，Auto Git 会停止。先让它解释现场
和安全选择，不要直接 reset 或 clean。

## 8. 准备一次 Commit

先告诉 Agent 这次要提交哪些文件：

> 帮我检查这次修改，只提交 `文件A` 和 `文件B`。运行项目匹配的测试，给我看文件清单、
> Commit message、风险和恢复入口；我确认后再 Commit。

Auto Git 的流程是：

1. 重新读取 HEAD、分支、工作区和暂存区；
2. 固定你批准的精确文件；
3. 运行受信项目回归；
4. 生成不可变计划和 hash；
5. 等待你确认同一份计划；
6. 只暂存批准文件；
7. Commit 后验证 HEAD 和提交范围；
8. 保存脱敏 operation record。

### 预期结果

- Commit 中只有你确认的文件；
- 测试结果可见；
- Commit OID 和文件范围经过 postflight；
- 工作区其他文件保持原样。

### 遇到问题

如果文件、HEAD、暂存区或测试配置在预览后变化，旧计划会失效。让 Auto Git 重新
inspect 并生成新计划，不要绕过漂移保护。

## 9. 连接远程仓库

已有 GitHub 或 Gitee 仓库时，可以说：

> 帮我连接这个远程仓库：`远程URL`。Remote 名称先用 origin。检查 URL、账号、
> 远端是否为空和当前历史，不要 Push。

需要 GitHub 新仓库时，可以说：

> 帮我准备创建 GitHub 仓库。先确认 Owner、仓库名和 public/private 可见性；创建仓库
> 和 Push 分开审批。

Gitee 首版使用标准 Git Remote。没有受控 Gitee 建库适配器时，先在 Gitee 官方页面
创建空仓库，再把确认后的 URL 交给 Auto Git。

### 预期结果

Remote URL、Provider、Owner、仓库身份和远端初始状态经过验证；尚未公开本地代码。

### 遇到问题

如果 URL 中含用户名、密码或 Token，停止并改用系统凭证库、SSH 配置或官方登录流程，
不要把凭证发给 Agent。

## 10. 第一次 Push

第一次 Push 前说：

> 帮我检查当前分支第一次 Push 到 origin 是否安全。先 fetch，检查测试、远端分支、
> upstream 和 ahead/behind，给我看 Push 计划。

首次 Push 会设置 upstream，但只有在远端为空或历史与计划一致时继续。

### 预期结果

- 本地测试通过；
- 目标 remote 和 branch 明确；
- Push 后重新读取远端 ref；
- 远端 branch OID 与本地 HEAD 一致；
- upstream 指向正确远端分支。

### 遇到问题

如果远端已有不同历史，Auto Git 会停止。不要 force push；先确认远端内容来源和安全
同步方案。

## 11. 后续 Push

以后可以说：

> 帮我检查这次修改是否可以 Push。先 fetch、运行测试、检查 ahead/behind 和远端 OID，
> 给我看计划。

Auto Git 遇到以下情况会阻断：

- 本地 behind；
- 本地与远端 diverged；
- non-fast-forward；
- 工作区或计划漂移；
- 回归失败；
- 认证或网络结果不确定。

### 预期结果

只有远端 postflight 证明目标分支指向预期 Commit，Auto Git 才报告 Push 成功。

### 遇到问题

网络中断时不要盲目重复 Push。先让 Auto Git verify 远端 OID，判断上一次 Push 是
成功、失败还是 unknown。

## 12. Tag 和 GitHub Release

发布前先检查：

> 帮我检查 0.1.0 是否可以发布。验证版本、CHANGELOG、完整测试、构建、Release notes、
> assets 和同名 Tag；先不要创建 Tag 或 Release。

准备完成后，以下动作分别确认：

1. Release Commit；
2. annotated Tag；
3. branch Push；
4. 单个 Tag Push；
5. GitHub Release。

GitHub Release 必须引用已经在远端验证存在的 Tag，不允许平台隐式创建 Tag。

### 预期结果

版本、CHANGELOG、Release Commit、远端 branch、annotated Tag、Release 页面和 assets
相互一致。

### 遇到问题

如果中途失败，让 Auto Git 读取 checkpoint：

> 帮我 verify 上一次发布，告诉我哪些步骤已经公开、哪些尚未完成，并生成安全 resume
> 计划。不要删除远端 Tag 或改写历史。

Auto Git 会同时核对本地 annotated Tag、远端 Tag 和明确 `owner/repo` 下的 GitHub
Release。Release 完全一致时会报告已经完成，不会重复创建；如果标题、说明、草稿/
预发布状态、target、asset 名称或 SHA-256 内容摘要冲突，它会停止并解释差异，不会
覆盖现有 Release。

## 13. 失败与恢复

常用恢复请求：

> 帮我检查 Auto Git 上一次操作记录，先给我无损恢复计划，不要删除工作区文件。

Auto Git 只处理自己拥有且没有漂移的资产，例如：

- Commit 前恢复本次操作保存的 index；
- 读取本次失败、部分完成或结果未知记录，先核对实际状态；
- 解释无法安全自动恢复的现场。

当前脚本没有工作区单文件恢复、恢复ref或soft-uncommit的受管动作；需要时明确交接
经过核验的标准Git方案。暂存区恢复不能冒充这些能力。检查及结果状态见
[安全核验与继续方式](../../../../references/verification-status.md)。

### 预期结果

工作区文件仍在，恢复动作有明确 ownership 和 postflight。

### 遇到问题

如果 Auto Git 无法证明某个分支、Worktree 或 Tag 属于本次操作，它只提供 explain-only，
不会自动删除。

## 14. 更新 Auto Git

```bash
npx skills update auto-git
```

可以说：

> 帮我更新 Auto Git。先显示当前版本、目标版本、安装范围和变化，更新后重新验证宿主
> 发现、contract、scripts 和 doctor。

### 预期结果

版本更新完成，当前宿主仍能发现 Auto Git，doctor 与基本只读检查通过。

### 遇到问题

更新失败时保留原版本或明确报告无法恢复的原因，不留半套文件。

## 15. 卸载 Auto Git

```bash
npx skills remove auto-git
```

可以说：

> 帮我从当前项目卸载 Auto Git。只删除标准安装器拥有的 Skill 文件，保留项目文件、
> Git 历史、远程仓库和操作记录。

### 预期结果

指定范围不再发现 Auto Git；项目代码、Commit 历史和 Remote 不变。

### 遇到问题

如果同时存在 project 和 global 安装，先确认要移除哪一层，不要批量删除所有 Skill。

## 16. 常见问题

### 安装后会自动提交所有修改吗？

不会。Auto Git 不在后台运行，不会因文件变化自动 Commit 或 Push。你需要在 Agent
对话中提出目标，并在每个写入或公开动作前确认。

### 任何文件夹都能使用吗？

可以检查普通文件夹和 Git 仓库。普通文件夹需要你批准后才能 init；已有仓库会保留
原历史和工作方式。

### 能用 Gitee 吗？

可以连接标准 Gitee Git Remote 并 Push。首版的专用账号、API 建库和 Release Provider
仍以 GitHub 为先；Gitee 仓库可以由你在官方页面创建后交给 Auto Git 连接。

### 能在 Obsidian 里使用吗？

只要 Obsidian 中的 Agent 宿主能够加载标准 Skills、读取目标目录并运行本机命令，就
可以使用。Auto Git 本身不是 Obsidian 插件。

### Agent 停止是不是失败？

不一定。状态漂移、测试失败、远端分叉、审批缺失或恢复所有权不足时主动停止，是
Auto Git 的安全结果。先阅读原因，再决定下一步。

## 17. 如何判断成功

不要只看 Agent 说“完成”，请检查：

- doctor 报告具体 executable、版本和 capability；
- Commit 文件清单与批准范围一致；
- 测试结果真实通过；
- Push 后远端 branch OID 与本地 HEAD 一致；
- Tag target 指向正确 Commit；
- GitHub Release 引用已验证 Tag；
- 失败后的文件仍存在；
- operation record 能再次 verify；
- 用户手册、README 和当前版本一致。

如果证据不足，可以说：

> 请不要只总结结果。重新读取本地和远端事实，逐项告诉我验证证据；不确定的地方标记
> unknown，不要猜测成功。

## 18. 获取帮助

- GitHub 主仓库：<https://github.com/wukongai/auto-git>
- 发布后问题反馈：<https://github.com/wukongai/auto-git/issues>
- 中文 README：[`README.md`](../../../../README.md)
- English README：[`README.en.md`](../../../../README.en.md)

提交问题时请包含操作目标、脱敏后的错误、系统类型和 Auto Git 版本；不要附 Token、
密码、Cookie、私钥或带凭证的 Remote URL。
