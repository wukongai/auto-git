# 2026-08-03 Auto Git 标准 Skill 双远程发行 Design

状态：Accepted（用户于 2026-08-03 确认）

关联：

- [Auto Git 0.1.0 Spec](../../specs/auto-git-v0.1.0/spec.md)
- [Auto Git 0.1.0 PRD](../../../product/prd/auto-git-v0.1.0.md)
- [ADR 0004：Skill-first 产品形态](../../adr/0004-skill-first-product-and-authoring-boundary.md)
- [ADR 0005：标准 Skill 双远程发行](../../adr/0005-standard-skill-dual-remote-distribution.md)

## 1. 已固定的用户意图

Auto Git 是完整、独立、通用的 Git 产品。它未来可以作为 Git 训练营的一项交付内容，
但训练营不进入 Auto Git 的产品功能、安装包、运行模式或版本边界。

用户安装的是标准 Auto Git Skill。安装与升级遵循 Agent Skills 生态的标准 Git
仓库安装方式，不创建 `install.sh`、`install.ps1`、独立 pipx CLI、MCP Server 或
Auto Git 私有安装协议。

Auto Git 自身发布到两个远程仓库：

- GitHub：主发行仓库、标准简写安装源、GitHub Release Provider；
- Gitee：同源镜像仓库、国内网络环境的标准 Git URL 安装源。

## 2. 候选方案

### A. 单一 Skill 源码，GitHub 主源 + Gitee 同提交镜像

- 仓库根 `SKILL.md` 是标准发现入口；
- `scripts/`、`references/`、contract 和测试随仓库版本化；
- GitHub 与 Gitee 指向相同 Commit 和相同 annotated Tag；
- 用户通过标准 Skills CLI 从任一仓库安装；
- GitHub/Gitee 只改变获取地址，不改变安装后的 Skill 内容。

优点：产品、源码和版本真相源唯一；符合用户指定的标准安装方式；国内外网络均有入口。
代价：发布时必须验证双远程 Commit/Tag 一致，不能只凭 Push 命令退出码声称同步。

### B. GitHub/Gitee 分别维护两个发行目录

优点：可针对平台写不同内容。缺点：两个 Skill 内容、版本和文档会漂移，用户无法判断
哪一份是产品真相源。

### C. 自建 Shell/PowerShell 安装器

优点：可以控制文件复制流程。缺点：重复宿主 Skill 安装器的职责，引入 PATH、权限、
Shell、Windows 策略、升级和卸载维护面，也偏离标准 Agent Skill 分发。

## 3. 决策

选择方案 A。

### 3.1 发行拓扑

```text
Auto Git 本地保存项目
  └─ 同一个 main Commit / annotated Tag
       ├─ GitHub 主仓库（remote: origin）
       │    ├─ GitHub 标准 Skill 安装源
       │    └─ GitHub Release
       └─ Gitee 镜像仓库（remote: gitee）
            └─ 标准 Git URL Skill 安装源
```

`origin` 和 `gitee` 是本项目计划采用的本地 remote 名称。真实 Owner、URL、可见性和
默认分支必须在创建远程仓库前由机器事实与用户选择固定，Design 不猜测。

### 3.2 标准安装契约

GitHub 主源：

```bash
npx skills add <github-owner>/auto-git
```

Gitee 镜像：

```bash
npx skills add https://gitee.com/<gitee-owner>/auto-git.git
```

常用范围和宿主参数：

```bash
npx skills add <source> -g -a codex -a claude-code
```

- `<source>`：GitHub 简写或 Gitee 完整 Git URL；
- `-g`：安装到用户级，使 Skill 可用于多个项目；
- `-a codex`：暴露给 Codex；
- `-a claude-code`：暴露给 Claude Code；基于 Claude Code 的 WorkBuddy 复用该宿主通道。

项目级安装不传 `-g`。安装路径、复制/软链接、升级锁和卸载 ownership 由标准 Skills
CLI 或宿主原生 Skill 管理器负责，Auto Git 不重新实现。

升级和卸载使用标准命令：

```bash
npx skills update auto-git
npx skills remove auto-git
```

最终 README 必须逐条解释命令、参数、影响范围和前置条件。

### 3.3 无 Git 用户边界

Auto Git Skill 的获取和系统 Git 的安装是两个阶段，但当前标准仓库路径要求 Git 在先。
2026-08-03 对 `vercel-labs/skills` 官方源码的复核确认：非 blob allowlist 的普通
GitHub owner/repo 会调用 `cloneRepo`，Gitee 完整 Git URL 也会 clone。因此顺序固定为：

1. 尚未安装 Auto Git 时，由当前宿主 Agent 只读检测系统 Git；
2. Git 缺失时，宿主 Agent 展示系统官方/受信任包管理器安装计划、权限和影响；
3. 用户批准后安装 Git，并用 `git --version` 与 PATH 复验；
4. 使用标准 Skills CLI 从 GitHub/Gitee 仓库安装 Auto Git；
5. Auto Git 首次触发后运行自己的 `doctor`，复验 Git、Python、GitHub CLI、identity
   和 Provider capability。

不得宣传“尚未安装的 Auto Git 先运行并为自己安装 Git”，也不能用自建 `install.sh`
或私有 Release ZIP 掩盖标准 CLI 的前置条件。

### 3.4 双远程发布门禁

首次上库和后续版本发布必须按以下顺序：

1. 本地全量回归、Skill Engineering 门禁和凭证扫描通过；
2. 显式列文件 Stage，禁止 `git add -A` 和 `git add .`；
3. 首次 Commit 单独审批；
4. GitHub 与 Gitee 远程仓库分别创建或连接，并验证 Owner、仓库名、可见性和 URL；
5. 添加 `origin` 与 `gitee` 后分别 fetch/读取远端事实；
6. Push GitHub 与 Push Gitee 分别预览和审批；
7. 使用远端 ref/OID 验证两边目标分支指向同一本地 Commit；
8. annotated Tag、Tag Push 和 GitHub Release 分别审批；
9. 若 Gitee 同步 Tag，则验证两边 Tag 名与 peeled target Commit 一致；
10. 任一远程失败时保留已成功事实，不 force push、不删除公开资源，生成 resume 计划。

双远程验收的真相不是“命令成功”，而是：

```text
local HEAD OID
  = GitHub remote branch OID
  = Gitee remote branch OID
```

版本发布时还必须满足：

```text
local annotated Tag target
  = GitHub Tag target
  = Gitee Tag target（当本版本同步 Tag）
```

### 3.5 Provider 边界

双远程发行不等于在 0.1.0 新增 Gitee Provider Adapter：

- 标准 Remote、fetch、branch Push 和 Tag Push 使用 Git Core；
- GitHub 继续是首个专用 auth/repo-create/Release Adapter；
- Gitee 专用账号登录、API 建库、Release API 仍留在 Backlog；
- 若当前没有安全、可审计的 Gitee 建库适配器，远程仓库由用户在 Gitee 官方界面创建，
  Auto Git 只连接已确认 URL；
- 任何 GitHub/Gitee Token、密码、Cookie 或私钥都不进入聊天、仓库或 operation record。

## 4. 交付物

`0.1.0` 发行面新增或修订：

- 标准仓库根 Skill 结构；
- GitHub 与 Gitee 两套安装命令；
- project/global 与 Codex/Claude Code 宿主矩阵；
- 安装、升级、卸载和首次 `doctor` 教程；
- 双远程发布/验证/resume 契约；
- 干净环境标准安装测试；
- GitHub/Gitee 分支与 Tag OID 一致性测试；
- README、PRD、Spec、Architecture、Roadmap、Task、ADR、Sprint、测试报告和 Release 文档对齐。
- `README.md` 中文入口与 `README.en.md` 英文入口；
- `docs/knowledge/users/guides/auto-git-user-manual.zh-CN.md` 中文用户手册；
- OB `_OB工程/publications/auto-git/Auto Git 用户手册.md` 布丁发布副本；
- 布丁 dry-run、apply、status、公开 URL 与仓库/OB 正文一致性证据。

不新增：

- 训练营模式或课程包；
- `install.sh` / `install.ps1`；
- Auto Git 私有安装器；
- Gitee 专用 Release Provider；
- 自动 Commit、自动 Push、force push 或自动公开发布。
- 布丁环境 ID、后台 URL 或同步时间进入公开 GitHub/Gitee 仓库。

## 5. 验收摘要

1. GitHub 和 Gitee 任一标准源安装后，Skill manifest 与版本一致；
2. Codex 与 Claude Code 能发现并触发 `auto-git`；
3. 标准安装、升级、卸载均不依赖 Auto Git 自建安装器；
4. Git 缺失时，Skill 获取事实和系统 Git 安装事实分层报告；
5. 双远程分支 OID 一致后才能报告源码同步完成；
6. Tag target 一致后才能报告版本 Tag 同步完成；
7. GitHub Release 必须引用已验证远端 Tag；
8. 任一远程中断后可根据 checkpoint 继续，不改写已公开历史；
9. 用户未分别批准时，不创建远程仓库、不 Commit、不 Push、不 Tag、不 Release。
10. 中英 README 关键语义一致，中文用户手册从标准安装覆盖到 Release/恢复；
11. 布丁只同步 OB 发布副本，仓库与发布正文一致且平台元数据隔离。

## 6. 用户确认

- 是否接受 GitHub 主源、Gitee 同提交镜像的单一真相源；
- 是否接受 Gitee 0.1.0 只承担标准 Git Remote/安装镜像，不新增专用建库和 Release API；
- 是否接受取消自建安装脚本与专用离线安装协议；
- 是否接受首次 Commit、双远程 Push、Tag 和 Release 继续分别审批。
- 是否接受 README 中英双版、中文用户手册和 OB→布丁受控发布副本的边界。

用户于 2026-08-03 确认以上全部边界，并要求 README 顶部可切换、两版完全从用户
视角说明；用户手册作为比 README 更具体的独立 Playbook，同步到布丁。
