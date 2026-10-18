# ADR 0005：Auto Git 采用标准 Skill 双远程发行

状态：Accepted（用户于 2026-08-03 确认）

日期：2026-08-03

## 背景

Auto Git 已固定为由 Skill Engineering 开发和治理、由最终用户独立安装的 Agent Skill。
此前 ADR 0004 把 GitHub Release Skill 归档作为无 Git 首次获取基线，并计划在 Git
可用后才支持标准仓库安装。用户进一步明确：

- Auto Git 应遵循 GitHub Agent Skill 的标准安装方式；
- 不需要 `install.sh`、`install.ps1` 或 Auto Git 私有安装协议；
- Auto Git 自身要发布到 GitHub 和 Gitee 两个远程仓库；
- Auto Git 可以作为训练营的一项交付，但训练营不是产品功能。

## 候选方案

### A. 标准 Git 仓库 Skill，GitHub 主源 + Gitee 同提交镜像

一个 Skill 源码、一套版本和测试；两个远程仓库只提供不同网络入口。安装交给标准
Skills CLI 或宿主 Skill 管理器。

### B. 两个平台维护不同发行目录

可以做平台定制，但会产生版本和内容漂移，不再有唯一产品真相源。

### C. 自建跨平台安装器

可以复制文件，但重复宿主能力并扩大权限、Shell、升级和卸载维护面。

## 决策

选择方案 A。

1. Auto Git 的正式安装对象仍只有 Auto Git Skill。
2. GitHub 为主发行仓库，Gitee 为同源镜像仓库；两者必须发布同一 Commit 和同一版本。
3. GitHub 标准安装源使用仓库简写；Gitee 使用标准完整 Git URL。
4. project/global 范围、Codex/Claude Code 宿主目标、复制或软链接、升级和卸载由标准
   Skills CLI/宿主安装器负责。
5. 不创建 `install.sh`、`install.ps1`、独立 pipx CLI、MCP Server 或 Auto Git 私有
   安装清单协议。
6. GitHub 自动生成的源码归档或 Release asset 可以作为校验/审计产物，但不再是
   `0.1.0` 的首要安装契约。
7. GitHub 继续是 `0.1.0` 唯一专用 Provider Adapter；Gitee 通过标准 Git Remote
   connect/fetch/Push/Tag Push 支持，专用登录、API 建库和 Release API 继续延后。
8. 双远程发布成功必须用分支 OID 和 Tag target 验证，不能只依赖命令退出码。
9. Commit、GitHub remote、Gitee remote、两次 Push、Tag、Tag Push 和 GitHub Release
   继续遵守独立计划、审批、record 与 postflight。
10. 训练营不进入 Auto Git 的功能、安装或版本模型。
11. 仓库 README 提供中文和英文两版；中文用户手册保存在仓库并投影到 OB 发布副本。
12. 布丁同步元数据只留在 OB，公开仓库不保存 `pudding_id`、后台 URL 或同步时间。

## 后果

### 正向

- 用户使用生态标准命令安装、升级和卸载；
- 产品不维护额外安装器；
- GitHub/Gitee 为同一产品提供国内外获取入口；
- Provider-neutral Git Core 可直接支撑镜像同步；
- 训练营可以交付正式产品，不产生训练营分叉版本。

### 代价

- 必须验证标准 Skills CLI 的真实 Git/Node/宿主前置条件；
- 必须增加双远程 OID/Tag 一致性和中断恢复测试；
- Gitee 没有专用 Adapter 时，首次建库可能仍需用户通过官方界面完成；
- 发布流程多一个需要独立验证的公开远程。

### 2026-08-03 前置条件验证结果

`vercel-labs/skills` 官方 `src/add.ts` 与 `src/git.ts` 显示：普通 GitHub owner/repo
不在 blob allowlist 时调用 `cloneRepo`；GitLab、Gitee 等 Git URL 也直接 clone。
因此 Git 是 Auto Git 标准仓库首装前置条件。无 Git 新手先由已存在的宿主 Agent
通过系统官方入口准备并验证 Git，再运行 `npx skills add`。这仍遵守“标准安装、无
私有安装器”的本 ADR 决策。

## 修正的旧决策

- 修正 ADR 0004 第 6 条：标准仓库型 Skill 安装成为 `0.1.0` 基线，不再以 Auto Git
  私有 GitHub Release 归档安装流程作为首要契约。
- 保留 ADR 0003 的 GitHub-first Provider 决策；Gitee 镜像不等于新增 Gitee Provider。
- 保留 ADR 0004 的 Skill-first、bundled scripts、无独立 CLI/MCP 决策。

## 验证要求

- GitHub/Gitee 安装源发现相同 `auto-git` Skill；
- 两源安装后的版本、manifest 和关键文件 hash 一致；
- project/global、Codex/Claude Code 安装矩阵通过；
- 无 Git clean environment 的标准安装前置条件被真实验证，并固定“宿主先装 Git →
  标准 Skills CLI 安装 Auto Git”的顺序；
- 双远程 branch OID 和同步 Tag target 一致；
- 任一远程失败时 resume 不 force push、不删除公开资源。
