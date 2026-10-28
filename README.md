[中文](README.md) | [English](README.en.md)

# Auto Git

**把你想做的事告诉 Agent，让 Auto Git 用标准 Git 安全完成。**

Auto Git 是一个面向普通用户的 Agent Skill。你不需要记住 Git 命令，只需要告诉
Codex、Claude Code 或兼容 Agent：“检查这个项目”“准备一次提交”“连接远程仓库”
或者“发布这个版本”。Auto Git 会先读取真实状态、解释影响、运行项目测试，再在需要
写入或公开内容时请你确认。

当前版本：**0.1.0-dev.1 安全修复候选**。已有GitHub备份记录；标准安装试用仍待验收，
Gitee镜像、正式Tag/Release及跨宿主试用尚未闭环。安全检查和状态含义见[核验说明](references/verification-status.md)。

## 你可以用它做什么

- 检查电脑是否具备 Python、Git 和 GitHub CLI；
- 指导安装 Git，并检查提交姓名和邮箱；
- 为新文件夹初始化标准 Git 仓库；
- 查看当前分支、改动、暂存区和远程状态；
- 只把你确认的文件加入一次 Commit；
- 连接 GitHub、Gitee 或其他标准 Git Remote；
- 在 Push 前检查测试、upstream、ahead/behind 和远端分叉；
- 分阶段准备版本、Tag、Push 和 GitHub Release；
- 操作失败后保留文件，并根据记录继续或恢复。

## Auto Git 不会做什么

- 不会在后台监控文件夹；
- 不会自动 Commit 或 Push；
- 不会未经确认创建远程仓库、Tag 或 Release；
- 不会执行 `git add -A`、force push、`reset --hard` 或删除未知文件；
- 不会接收、打印或保存 Token、密码、Cookie 和私钥；
- 不会要求你额外安装 Skill Engineering、独立 Auto Git CLI 或 MCP Server。

## 安装 Auto Git

你需要先有一个支持 Agent Skills 的宿主、可以运行 `npx` 的 Node.js 环境，以及系统
Git。标准仓库型 Skills CLI 会用 Git 获取 Auto Git，所以真实首装顺序是：
**先准备 Git，再安装 Auto Git**。你不需要掌握 Git 命令，可以先对当前宿主 Agent 说：

> 我的电脑可能没有 Git。请用系统官方方式检查并指导安装，解释权限和影响；安装后
> 运行 git --version 验证。先不要初始化项目、Commit 或 Push。

这一步发生在 Auto Git 安装之前，由宿主 Agent 和系统官方安装入口完成。Auto Git
安装后会重新运行 doctor，并在以后每个项目中接管 Git 检查、计划、验证和恢复。

> **安装验收提示：** 以下为声明的标准安装入口。GitHub已有备份记录，本轮尚未验证
> 安装源的实时可用性或将安全候选推送远端；安装试用仍待验收。不要替换为来源相似的同名仓库。

### 安装到当前项目

```bash
npx skills add wukongai/auto-git
```

这条命令从 [GitHub 主仓库](https://github.com/wukongai/auto-git) 安装 Auto Git，
默认只对当前项目生效。

### 安装到所有项目

```bash
npx skills add wukongai/auto-git -g -a codex -a claude-code
```

- `-g`：安装到当前用户范围，让多个项目都能使用；
- `-a codex`：暴露给 Codex；
- `-a claude-code`：暴露给 Claude Code；基于 Claude Code 的 WorkBuddy 复用此通道。

Global 安装会影响你的多个项目，执行前应确认安装范围。

### Gitee 镜像

Auto Git 采用 GitHub 主源和 Gitee 同提交镜像。Gitee 的正式安装 URL 会在首次镜像
仓库创建并验证后回填；在此之前不要使用未经验证的同名仓库。

Auto Git 不提供额外的操作系统安装器，安装、更新和卸载都走标准 Skills CLI 或宿主
原生 Skill 管理器。

## 第一次使用

打开一个项目，然后把这句话交给 Agent：

> 帮我用 Auto Git 检查这个项目。只读检查环境和仓库状态，告诉我缺少什么，先不要修改。

Auto Git 会分别告诉你：

1. Skill 是否被当前 Agent 发现；
2. Python、Git 和 GitHub CLI 是否可用；
3. 当前目录是不是 Git 仓库；
4. 当前分支和文件改动；
5. 下一步建议，以及哪些动作需要你确认。

如果缺少 Git，可以说：

> 帮我按当前系统生成 Git 安装计划，解释权限和影响；我确认后再安装，安装后重新检查。

## 日常使用

### 准备一次 Commit

> 帮我检查这次修改，只提交我确认的文件。先运行项目测试并给我看 Commit 计划。

Auto Git 会显示文件清单、测试结果、提交说明和恢复入口。只有你确认同一份计划后，
它才会精确暂存并 Commit。

### 连接远程仓库

> 帮我连接这个 GitHub 或 Gitee 仓库。先检查 URL、账号、远端是否为空，不要 Push。

连接 Remote 和 Push 是两个独立动作，不会因为添加了远程地址就自动公开代码。

### Push

> 帮我检查当前分支能不能 Push。先 fetch、检查 ahead/behind 和测试，给我看计划。

如果远端领先、历史分叉、测试失败或状态发生变化，Auto Git 会停止，而不是自动
pull、rebase、merge 或 force push。

### 发布版本

> 帮我检查 0.1.0 是否可以发布。先检查版本、变更日志、测试、构建和 Tag，不要直接发布。

Release Commit、annotated Tag、分支 Push、Tag Push 和 GitHub Release 分别确认。
中途失败时，Auto Git 会读取已经公开的事实，从未完成的步骤继续。

## 更新和卸载

更新：

```bash
npx skills update auto-git
```

这条命令检查并更新已安装的 Auto Git。更新后应重新验证宿主发现、版本和 doctor。

卸载：

```bash
npx skills remove auto-git
```

这条命令移除标准安装器拥有的 Auto Git Skill，不删除你的项目文件、Git 历史或远程
仓库。Global 安装请先确认要移除的作用范围。

## 用户手册

需要按步骤完成第一次安装、Commit、Remote、Push、Release 或恢复，请阅读：

[《Auto Git 用户手册：从第一次检查到安全发布》](docs/knowledge/users/guides/auto-git-user-manual.zh-CN.md)

README 负责让你快速开始；用户手册是一份更具体的操作 Playbook，包含可以直接复制给
Agent 的话术、预期结果和常见问题处理。

## 支持范围

- Skill 宿主：Codex、Claude Code；WorkBuddy 通过 Claude Code 通道使用；
- 系统策略：macOS、Windows、Debian/Ubuntu、Fedora/RHEL；
- 远程：标准 Git Remote；GitHub 提供首个专用仓库与 Release 适配；
- 历史基线：114 项根项目自动测试、91 项纯 Skill 候选测试和临时仓库场景通过；
- 当前安全修复另有新增回归，完整验证随维护记录交付；历史数量不作为当前结果；
- 尚待首发验收：真实 GitHub/Gitee 双远程、正式 Tag/Release、跨宿主安装试用。

## 获取帮助

- 使用问题：发布后通过 [GitHub Issues](https://github.com/wukongai/auto-git/issues)；
- 产品与安全边界：[用户手册](docs/knowledge/users/guides/auto-git-user-manual.zh-CN.md)；
- 开发者事实源：[PRD](docs/product/prd/auto-git-v0.1.0.md)、[Architecture](docs/engineering/architecture/auto-git.md)、
  [Roadmap](docs/product/roadmap.md)。

请把错误原样交给 Agent，并要求它先诊断、保留文件、解释影响，再提出修复计划。
