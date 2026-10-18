# Auto Git Roadmap

## 版本总览

| 版本 | 状态 | 核心目标 |
|---|---|---|
| `0.1.0` | Local distribution candidate verified | 标准 Skill 双源安装、Git 初始化、本地 Commit、标准 Remote、Push、GitHub Release、验证与恢复 |
| `0.2.0` | Backlog | GitLab/Gitee 专用适配器、PR/CI 模板与更多发布产物 |
| `0.3.0` | Backlog | 多宿主兼容、分级反馈、沙盒验证和错误解释 |
| `0.4.0` | Backlog | 跨项目策略、ANK 推荐接入与可选形态复评 |
| `1.0.0` | Future | 稳定配置、计划、记录、兼容、安装、恢复和发布契约 |

## `0.1.0`：Zero-to-Release Guided Automation

### 必须回答

- Auto Git Skill 的宿主发现、安装范围、无 Git 获取和升级/卸载方式；
- GitHub 主源、Gitee 镜像及双远程 OID/Tag 一致性；
- README 中英双版、中文用户手册和布丁发布副本；
- Skill Engineering 开发治理与 Auto Git 运行时的边界；
- Skill 内确定性 `scripts/` 的实现语言和运行时；
- Python、Git 与 GitHub CLI 的检测、安装、升级和验证策略；
- Agent Skill 与确定性核心的接口；
- 仓库事实、计划、记录和漂移 schema；
- 当前分支、功能分支和 Worktree 的自动选择规则；
- 项目回归档位和命令信任模型；
- stage/Commit 的精确文件范围；
- Remote 创建/连接、认证边界、ahead/behind 和 Push；
- 版本来源、Release Commit、annotated Tag、Tag Push 和 GitHub Release；
- 失败后的恢复和幂等；
- 普通用户反馈与基础教学。

### 最小可信场景

1. 无 Git 环境得到正确的安装计划，安装后验证版本和 PATH；
2. 无 Git 干净环境先由宿主 Agent 指导安装并验证 Git，再从 GitHub/Gitee 标准源
   获取相同 Auto Git 内容，验证发现、升级和卸载；
3. Git identity 缺失时引导 local/global 配置并验证来源；
4. 新目录初始化 Git；
5. 干净小改动在当前功能分支提交；
6. 主分支功能开发转入独立分支或 Worktree；
7. 脏工作区保护已有用户改动；
8. 回归失败阻止 Commit；
9. Commit 后验证记录与实际仓库一致；
10. 创建或连接远端前展示 Owner、名称、可见性和 URL；
11. 首次 Push 设置 upstream，后续 Push 校验 ahead/behind；non-fast-forward 阻断；
12. Release readiness 阻断版本、变更日志、回归或构建不一致；
13. annotated Tag、branch Push、Tag Push、GitHub Release 分别审批并可断点恢复；
14. Auto Git 使用自身完成一次零到 Release 自举；
15. 至少一个普通项目完成可信接入。
16. 中文/英文 README 语义一致，中文用户手册完成零到 Release 基本教程并同步布丁。

本地 release candidate 已覆盖上述场景的确定性核心、临时仓库和 fake provider 验证。
当前宿主真实样本已完成 inspect → plan → exact Commit → verify；Auto Git 自身首次
Commit、真实 GitHub/Gitee Remote/Push、Tag、GitHub Release 和跨宿主安装试用属于
发布审批阶段，不能用本地测试替代。

### 不进入

- 未经批准的 Push、tag 或 Release；
- PR、merge 和包注册表发布；
- 后台守护进程；
- GitLab、Gitee 等专用仓库创建和 Release Adapter；
- 训练营课程、训练营专用安装包或训练营模式；
- MCP Server、独立 pipx CLI 和 Skill Engineering 运行时集成。

## 后续集成顺序

1. Auto Git 自身；
2. 一个普通本地项目；
3. ANK 中增加可选推荐或接入模板；
4. Skill Engineering 仓库作为普通受管项目验证；
5. 更多代码、内容和 Agent Skill 项目。

## 发布规则

- 功能开发先有 Spec、Plan，跨版本选择写 ADR；
- 旧项目接入必须保留现有 Git 历史和工作方式；
- 本地门禁、远程 CI 和真实用户效果分别报告；
- Commit、Push、远程仓库创建、tag、Release 和 Global 安装分别审批。
