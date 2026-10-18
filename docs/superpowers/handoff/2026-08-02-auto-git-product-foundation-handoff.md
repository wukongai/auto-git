# Handoff：Auto Git 独立产品基础

日期：2026-08-02

状态：Local distribution candidate verified; public Git release approvals pending

## 唯一恢复入口

后续 Codex/Agent 任务从本文件恢复。不要要求用户重复确认已经固定的产品目标、独立
仓库、命名或 ANK/Skill Engineering 边界。

## 用户要完成什么

开发一个可独立开源、可安装到多种项目的 Auto Git 产品。只要用户使用 Agent 开发
或工作，就可以通过自然语言安全地进入 Git 生命周期，不必记命令或反复提醒 Agent
提交。Auto Git 可以作为 Git 训练营的一项正式交付，但训练营不是 Auto Git 的功能、
安装包或版本模式。

## 已确认决策

- 产品名：`Auto Git`。
- 目录、仓库和 Skill 名：`auto-git`。
- 路径：`/Users/aim5/Documents/CodingProject/auto-git`。
- Auto Git 是独立仓库、独立安装和独立运行的生产级 Agent Skill。
- ANK 负责工程化初始化，可以推荐 Auto Git；Auto Git 不依赖 ANK 运行。
- Skill Engineering 是已存在的上游 Skill 开发项目，负责创建、工程化和维护 Auto Git；
  用户不安装 Skill Engineering，Auto Git 运行时也不依赖它。
- 推荐形态：单一 Auto Git Skill + Skill 内 `scripts/` 确定性核心 + references/tests；
  不把独立 pipx CLI 或 MCP Server 作为 `0.1.0` 产品。
- 用户采用标准 Skill 安装、升级和卸载方式，不创建 `install.sh`、`install.ps1` 或
  Auto Git 私有安装协议。
- Auto Git 自身采用 GitHub 主发行仓库 + Gitee 同 Commit/Tag 镜像仓库；两个远程是
  同一产品的安装源，不是两套源码。
- 不强迫所有任务使用 Worktree；根据分支、脏状态、风险和并行情况选择。
- 回归测试定义“检查什么”；本地门禁和 Push/PR 后 CI 分层执行。
- 自动化不意味着无审批公开发布。
- 用户于 2026-08-03 选择方案 A：`0.1.0` 必须从 Git/Auto Git 安装走到 Push 和
  GitHub Release。
- 标准 Remote/Push 保持 Provider-neutral；GitHub 是首个账号、仓库创建和 Release
  专用适配器。
- Commit、remote create/connect、Push、Tag、Tag Push 和 Release 分别审批。
- GitHub/Gitee 两次 Push 分别审批；只有 branch OID 与同步 Tag target 一致时才报告
  双远程同步成功。
- README 提供中文与英文两版；新增纯用户视角的中文使用手册，并通过 OB 发布副本同步
  到布丁。布丁元数据不进入公开仓库。

## 当前工程状态

- ANK 已创建跨 Agent 工程化骨架和本机 Claude 项目记忆。
- 本地 Git 仓库已初始化，初始分支为 `main`。
- 当前版本事实源为 `0.1.0-dev.0`。
- Product、Constitution、Architecture、Roadmap、Task、Backlog、ADR 0001、Sprint
  和 Daily Log 已建立。
- `0.1.0` PRD 与 Spec 已由用户于 2026-08-03 以 Go 模式确认；ADR 0002、0003、
  0004 均为 Accepted。2026-08-03 新增的标准 Skill 双远程发行修订、Design、ADR
  0005 和 US-025 双语文档/布丁发布要求已由用户确认，TDD Plan 已创建。
- 用户于 2026-08-03 确认 Auto Git 本身是 Skill，Skill Engineering 是开发期创建和
  治理工具；ADR 0004 已记录该决定，PRD/Spec 已完成 Skill-first 修订并等待确认。
- Auto Git 产品开发 OB Task 已创建：
  `/Users/aim5/Documents/OB/04 Inbox/task/2026-08-02-【Auto Git】Auto Git 0.1.0 Skill 产品开发.md`。
  优先级 P1、状态 Doing，`today_history` 包含 2026-08-02 与 2026-08-03；飞书尚未
  同步，因为本机 `feishu-cli` 用户认证已过期。
- `.ai-native/profile.json` 已建立；10 个 ANK `.new` 与活跃文件已逐项审计，结论记录
  于 `docs/research/2026-08-03-ank-new-diff-audit.md`。用户 Constitution/Product/
  文档地图保持不覆盖；活跃 Claude rules/commands/settings 已合并必要 profile 值。
  `.new` 作为非覆盖生成证据保留，不是运行入口。
- Native Authoring Brief、TDD Plan、根 Skill、contract、references、scripts 和 tests
  已落地；最终 38 文件 candidate fingerprint 为 `73f6bb5f…51f07b60`，对应 Native
  Plan 为 `.skill-engineering/native-plan-auto-git-v0.1.0-final-review.json`。
- 标准安装、双语 README、中文用户 Playbook、双远程只读 postflight 和布丁 projection
  已按 RED → GREEN 落地；独立审查指出的恢复、Remote、CLI 和权限问题已修复，fresh
  验证为根项目 114 passed、纯 Skill 候选 91 passed、ruff/compileall pass。
- 官方 Skills CLI 源码已确认 Auto Git 的普通 GitHub/Gitee 仓库安装需要 Git：
  首次自举必须由宿主 Agent + 系统官方入口先准备 Git，再标准安装 Auto Git；不得
  恢复旧 Release ZIP 首装叙述。
- 修订后 38 文件精确候选通过 content gate（0 finding）、production creation review
  100/A、self-test 和最终 Native Plan apply/verify。GitHub 目标绑定、Release resume、
  Provider Tag OID、asset digest、operation 幂等、锁内二次校验、effective config/mode
  fingerprint、非 Git 目录递归 fingerprint、畸形 record fail closed 与 stale lock
  诊断已完成 TDD 加固；顶层 record 类型异常也统一返回结构化 drifted。
- 布丁 draft Case `cmscwjpjp00e5pokaitm2t42c` 已创建，后台 URL 为
  `https://aixiaoai.cloud/admin/cases/cmscwjpjp00e5pokaitm2t42c/edit`；没有公开 URL。
- 当前宿主临时普通项目完成 inspect → plan → exact Commit → verify。把 plan 写入目标
  仓库会触发漂移，计划应保存到仓库外状态目录。
- Auto Git 自身仍没有 Commit、Push、真实远程仓库、tag、Release 或 Global 安装。

## 必须先读

1. `AGENTS.md`
2. `docs/constitution.md`
3. `docs/PRODUCT.md`
4. `docs/PRD.md`
5. `docs/superpowers/specs/2026-08-02-auto-git-v0.1.0-spec.md`
6. `docs/ARCHITECTURE.md`
7. `docs/ROADMAP.md`
8. `docs/TASK.md`
9. `docs/adr/0001-independent-product-boundary.md`
10. `docs/adr/0002-python-core-and-json-contract.md`
11. `docs/adr/0003-zero-to-release-github-first.md`
12. `docs/adr/0004-skill-first-product-and-authoring-boundary.md`
13. `docs/adr/0005-standard-skill-dual-remote-distribution.md`
14. `docs/superpowers/specs/2026-08-03-auto-git-standard-skill-dual-remote-distribution-design.md`
15. `docs/sprints/2026-08-auto-git-product-foundation.md`

## 工作顺序

1. 读取已完成的 ANK `.new` 审计，不重复覆盖用户 Constitution/Product。
2. 只读盘点本机已有 Git Skills、scripts、hooks、CI 模板和相关工程；记录
   adopt/adapt/defer/reject，不复制已有实现。
3. 比较 2–3 个核心实现技术方案，重点评估 Skill-first bundled scripts、独立 CLI、
   MCP、安装、跨平台、Git 进程安全、schema、测试和 Skill/Scripts 调用边界。
4. 读取
   `docs/superpowers/testing/2026-08-03-auto-git-v0.1.0-test-report.md` 的 fresh 证据。
5. 读取已完成的
   `docs/superpowers/plans/2026-08-03-auto-git-standard-distribution-and-user-docs-plan.md`
   和测试报告，不重复实现。
6. 只读审查首次 Commit 范围和真实安装/Remote/Release 发布计划。
7. 基于最终源状态生成新的 Native Plan；不要沿用基线 fingerprint。
8. Commit、两边 Remote、两次 Push、Tag、Release、Global 安装分别请求独立批准。
9. 真实发布后补 release record、双远端 postflight 和跨宿主安装试用。

## `0.1.0` 必须覆盖

- repo inspect 和机器可读事实；
- immutable plan、fingerprint、drift 和操作记录；
- init、当前分支、功能分支和 Worktree 策略；
- 精确 staging，默认禁止 `git add -A`；
- 项目回归档位、命令信任和失败阻断；
- Commit 计划、审批、执行和 postflight；
- 不丢文件的恢复路径；
- Agent Skill 的自然语言、解释和基础训练模式；
- Auto Git 自举和至少一个普通项目可信场景；
- OS/Python/PATH/Git/GitHub CLI doctor；
- Git、GitHub CLI 的平台安装计划与安装后验证；
- Auto Git Skill 的宿主发现、安装范围、无 Git 获取、升级和卸载；
- GitHub/Gitee 标准安装源内容一致和双远程 OID/Tag 一致性；
- 中英 README、中文用户手册、OB 发布副本与布丁同步 postflight；
- Git identity 的 local/global 作用域配置与来源验证；
- GitHub 浏览器登录与凭证隔离；
- 标准 Remote create/connect 与 GitHub 仓库创建；
- 首次/后续 Push、ahead/behind、non-fast-forward 阻断与远端 postflight；
- release profile/readiness、Release Commit、annotated Tag；
- branch Push、单 Tag Push、GitHub Release 的独立审批和断点恢复。

## 暂不进入

- 未经批准的 Push、tag 或 Release；
- PR、merge、force push、自动解决冲突和包注册表发布；
- 后台监控全部文件夹；
- GitLab/Gitee 专用仓库创建、认证和 Release Provider；
- 训练营模式、训练营专用包或课程内容；
- 云服务、模型 Provider 和凭证托管；
- ANK 运行时集成；
- 独立 pipx CLI、MCP Server、root/admin 系统级安装与单二进制分发。

## 审批边界

本地实现、文档和验证已完成。当前会话没有获准实际 Commit、Push、创建远程仓库、
tag、Release 或安装任何组件；未来发布中的每类动作仍必须遵守各自审批门禁。
