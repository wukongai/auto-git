# Auto Git 0.1.0 产品需求文档（PRD）

状态：Proposed，等待用户与 `0.1.0` Spec 一并确认

版本：`0.1.0`

更新日期：2026-08-03

关联文档：

- [产品定义](../product-definition.md)
- [工程宪章](../../constitution.md)
- [目标架构](../../engineering/architecture/auto-git.md)
- [0.1.0 技术 Spec](../../engineering/specs/auto-git-v0.1.0/spec.md)
- [Roadmap](../roadmap.md)

## 1. 文档目的

本文回答四个问题：

1. Auto Git 为谁解决什么问题；
2. `0.1.0` 必须提供哪些产品能力；
3. 用户通过 Agent 如何从没有 Git 走到远端 Release；
4. 每个 User Story 在什么条件下才算验收通过。

技术 schema、scripts 接口、fingerprint、锁、执行和恢复细节以 `0.1.0` Spec 为准。PRD 与 Spec
冲突时，先按项目宪章处理，再由用户确认修正文档，不允许实现阶段自行选择解释。

## 2. 产品摘要

### 2.1 一句话价值

让使用 Agent 开发或工作的普通用户，即使没有安装 Git、不了解远端仓库和 Release，
也能从零开始安全、可解释、可恢复地完成版本管理和版本发布，并在真实操作中逐步
理解 Git。

### 2.2 产品承诺

Auto Git 不承诺“替用户无条件自动提交”，而是承诺：

- 先读取真实 Git 事实，不从聊天猜测；
- Auto Git Skill 尚未安装时，提供明确安装范围、来源和验证方法；
- 缺少 Git、Python 或 GitHub CLI 时，先解释安装来源、权限和验证方法；
- 先展示计划，再执行同一份未漂移计划；
- 只处理用户确认的文件与动作；
- 回归失败时阻止 Commit；
- 远端事实不足、分支落后或认证未就绪时阻止 Push；
- 版本、变更日志、Tag 或构建产物不一致时阻止 Release；
- 出错时保护工作区文件并提供可验证的恢复路径；
- 把关键 Git 决策解释成普通用户能理解的语言。

### 2.3 `0.1.0` 产品边界

`0.1.0` 是从空白环境到 GitHub Release 的最小可信纵向闭环：

```text
安装并发现 Auto Git Skill
→ 环境 doctor
→ Git / GitHub CLI 安装与验证
→ 仓库初始化与盘点
→ 工作区策略
→ 不可变计划
→ 用户审批
→ 精确 staging
→ 项目回归
→ Commit
→ 创建或连接 Remote
→ Push
→ Release readiness
→ Release Commit / annotated Tag
→ Push branch / Push Tag
→ GitHub Release
→ postflight / 操作记录 / 断点恢复
```

每个高风险动作仍独立审批。`0.1.0` 不执行 PR、merge、force push、自动冲突解决或
包注册表发布；不提供 GitLab/Gitee 专用仓库创建和 Release API，但可连接其标准
Git Remote 并 Push。

### 2.4 产品形态

Auto Git 本身是用户安装和使用的独立 Agent Skill，由 Skill Engineering 在开发期
创建和治理。它的确定性实现随 Skill 放在 `scripts/`，不是另一个要求用户单独安装的
Auto Git CLI；`0.1.0` 也不要求 MCP Server。

用户只需要安装 Auto Git Skill。Skill 加载后由根 `SKILL.md` 理解意图、解释风险和
请求审批，再调用自身 `scripts/` 读取事实和执行获批动作。Auto Git 运行时不调用或
依赖 Skill Engineering。

## 3. 需求分析

### 3.1 用户现状

目标用户通常知道“项目应该保存版本”，但难以稳定回答：

- 我的电脑有没有 Git、版本是否可用、应该从哪里安装；
- Auto Git 怎样安装、升级、卸载，是否会污染系统环境；
- 当前目录是不是 Git 仓库；
- 当前在哪个分支，是否正在主分支工作；
- 这次任务应该留在当前分支、创建功能分支还是使用 Worktree；
- 工作区里哪些文件属于本任务，哪些是之前留下的；
- Commit 前应该跑哪些检查；
- Agent 准备提交的文件是否准确；
- Remote 是什么、仓库应该建在谁的账号下、公开还是私有；
- 本地分支是否领先或落后，当前是否可以 Push；
- 版本号、Tag、Release 和发布产物是什么关系；
- Commit、Push、merge 和 Release 的风险为什么不同；
- 命令失败后如何恢复而不丢文件。

Agent 能运行 Git 命令，但自然语言模型本身不能成为仓库事实源，也不能只凭聊天记忆
承担计划一致性、并发锁、文件范围和恢复所有权。

### 3.2 核心痛点

| 痛点 | 直接后果 | Auto Git 的产品响应 |
|---|---|---|
| 不会安装 Git 或 CLI | 产品第一步就被环境阻断 | doctor + 官方来源安装计划 + 安装后验证 |
| 不知道真实仓库状态 | 在错误目录、错误分支或 detached HEAD 上操作 | 机器可读 inspect |
| Agent 忘记或随意选择 Git 流程 | 功能直接堆在主分支，或无意义地强制 Worktree | 可解释的工作区策略 |
| 写入前没有稳定计划 | 用户批准 A，Agent 实际执行 B | plan id + plan hash + drift |
| staging 范围过宽 | 把无关文件、凭证或半成品提交 | 精确路径 staging |
| 测试命令不可信或没执行 | 带病 Commit，聊天里却说“已通过” | 回归档位与命令信任 |
| Commit 成功与否只看一句输出 | 记录、HEAD 和实际提交范围不一致 | postflight + record |
| 不理解 Remote 与认证 | 连错仓库、公开性选错或泄露 Token | Remote plan + 系统凭证边界 |
| 把 Commit 当成已经上传 | 成果仍只在本机，或未经检查直接公开 | ahead/behind + 独立 Push 审批 |
| Release 步骤靠记忆 | Tag、版本、变更日志和产物不一致 | release readiness + 分阶段发布计划 |
| 恢复依赖危险命令 | `reset --hard`、`clean` 导致文件丢失 | ownership-aware recovery |
| Git 术语过多 | 用户只能反复依赖 Agent，无法把关 | 基于真实操作的分层解释 |

### 3.3 根因

1. **事实层缺失**：聊天和目录名不能证明 Git 状态。
2. **意图与执行混在一起**：自然语言 Agent 同时做判断、拼命令和执行，缺少稳定边界。
3. **审批粒度过粗**：一句“可以”被错误复用于 Commit、Push 或恢复。
4. **缺少漂移检测**：预览后文件、HEAD 或 index 变化，旧计划仍被继续执行。
5. **缺少恢复所有权**：工具不知道哪些 ref、index backup 或 Worktree 是自己创建的。
6. **教学脱离现场**：用户看到命令，却不知道命令和当前风险的关系。
7. **安装入口缺失**：默认用户已经有 Git、Python、PATH 和 Provider CLI，产品无法
   服务真正的新手。
8. **本地与公开动作混淆**：Commit、Push、Tag 和 Release 被包装成一次模糊批准，
   失败后也没有公开状态 checkpoint。

### 3.4 Jobs To Be Done

#### JTBD-01：安全保存当前成果

当我完成一段工作时，我希望 Agent 能确认哪些文件属于本次任务、运行正确的检查并
准备 Commit，这样我不需要记 Git 命令，也不会混入无关文件。

#### JTBD-02：选择合适的工作区

当我要开始功能、修复或并行任务时，我希望系统根据主分支、脏状态和风险推荐当前
分支、功能分支或 Worktree，这样我既得到隔离，也不会被流程仪式拖慢。

#### JTBD-03：理解并批准真实影响

当 Git 即将写入仓库时，我希望看到将执行的动作、文件范围、回归和恢复方式，这样我
批准的是一份明确计划，而不是模糊授权。

#### JTBD-04：失败后不丢工作

当测试、hook、Commit 或恢复失败时，我希望系统保留当前文件，解释失败阶段并提供
安全下一步，这样我不会因为一次自动化操作丢失成果。

#### JTBD-05：边做边学 Git

当 Agent 帮我完成版本管理时，我希望它说明“现在在哪里、为什么这样选、接下来会
发生什么、怎样恢复”，这样我能逐渐理解 Git 并对关键决策进行把关。

#### JTBD-06：从零准备可用环境

当我的电脑缺少 Git 或 Auto Git 时，我希望系统识别操作系统和已有工具，给出来自
官方来源、能看懂影响的安装方案，并在安装后验证，这样我不用先成为命令行专家。

#### JTBD-07：安全连接并同步远端

当我要把本地成果保存到远端时，我希望系统帮助我选择或创建正确仓库、检查认证和
分支差异，并在我单独批准后 Push，这样不会误传到错误账号或覆盖别人工作。

#### JTBD-08：发布一个可验证版本

当成果准备交付时，我希望系统检查版本号、变更日志、回归、构建和 Tag，分步骤完成
Push 与 GitHub Release，并在中断后告诉我已经公开了什么、下一步是什么。

## 4. 用户与角色

### 4.1 主要用户：Agent 协作型 Git 新手

- 使用 Codex、Claude Code 或其他 Agent 开发；
- 能理解文件、项目和功能，但不熟悉 Git 命令；
- 希望知道关键风险，不想背命令；
- 最担心误删文件、提交错内容和不知如何恢复。

### 4.2 次要用户：独立开发者或内容创作者

- 懂基本 Git，但不想每次提醒 Agent 做 status、回归、Commit；
- 同时维护代码、文档、Skill 或内容项目；
- 需要稳定、低打扰、可复用的本地门禁。

### 4.3 次要用户：项目维护者

- 希望把已有测试、lint、hooks 和分支约定接入 Auto Git；
- 不接受重写历史、替换 CI 或绑定特定 Agent；
- 需要审计“Agent 实际做了什么”。

### 4.4 系统角色：Agent Skill

Agent Skill 不是仓库事实源。它负责：

- 理解自然语言意图；
- 选择 Core 的固定参数；
- 呈现事实、建议、计划和审批；
- 把结果翻译成适合用户的解释。

它不得绕过 Core 直接执行写入型 Git。

## 5. 目标与成功标准

### 5.1 产品目标

1. 用户无需查 Git 命令即可完成环境准备、init、Commit、Remote、Push、Release 和恢复。
2. 所有写入动作都经过 preview/apply 分离与漂移复验。
3. Commit 只包含用户确认的精确路径。
4. 项目回归失败时不能生成成功 Commit。
5. Auto Git 自身造成的失败不删除用户工作区文件。
6. 用户能理解本次策略、审批边界和恢复入口。
7. Auto Git Skill、Git、Python 与 GitHub CLI 的安装来源、权限需求、范围和验证结果
   可审计。
8. Remote、Push、Tag 和 Release 的实际远端结果经过 postflight 验证。

### 5.2 `0.1.0` 发布成功标准

| 指标 | 发布门槛 |
|---|---|
| 写入流程计划覆盖率 | init、workspace、commit、recover 全部先 plan 后 apply |
| 环境引导 | 支持 macOS、Windows、Debian/Ubuntu、Fedora/RHEL 的 Git 检测和官方安装路径 |
| Auto Git 分发 | GitHub/Gitee 标准源安装内容一致；宿主发现、升级、卸载和无 Git 前置条件验证通过 |
| Git 首次配置 | identity 缺失 100% 阻断 Commit；local/global 作用域和来源可验证 |
| 漂移阻断 | HEAD、index、status、selected path 或配置变化均拒绝旧 plan |
| staging 精确度 | 集成测试中 staged set 与批准路径 100% 一致 |
| 回归阻断 | 失败、超时、命令缺失和未信任配置 100% 阻断 Commit |
| 文件保护 | Core 失败路径不删除工作区文件；外部 hook 副作用可检测且不覆盖 |
| Commit 验证 | 成功 Commit 100% 生成可独立 verify 的 record |
| 恢复所有权 | 只操作本 record 拥有且未漂移的 index/ref/Worktree |
| 可信场景 | Roadmap 的 15 个最小可信场景全部有验证证据 |
| 普通项目接入 | 至少 1 个非 Auto Git 项目保留原历史、测试和工作方式完成闭环 |
| 自举 | Auto Git 使用自身完成一次本地闭环 |
| Remote 安全 | create/connect 的 Owner、仓库名、可见性、URL 和认证状态均先预览 |
| Push 安全 | upstream、ahead/behind、fetch 结果、回归与目标 ref 均通过 postflight |
| Release 一致性 | 版本、变更日志、Release Commit、annotated Tag、远端 Tag 和 GitHub Release 一致 |
| 断点恢复 | Push/Tag/Release 任一步中断后能根据远端事实安全 resume，不重复公开动作 |

`0.1.0` 不采集云端增长、活跃度或用户行为数据；操作记录默认留在本机，Provider
只接收完成用户已批准公开动作所需的数据。

## 6. 范围与优先级

### 6.1 Must Have（发布阻断）

- Git / 非 Git 目录 inspect；
- init plan/apply/verify；
- 当前分支、功能分支和 Worktree 策略；
- 脏工作区保护；
- immutable plan、fingerprint、drift、lock、idempotency；
- 精确 staging，禁止全量 add；
- 回归档位和配置 fingerprint 信任；
- Commit 审批、执行和 postflight；
- 操作记录和 verify；
- 不丢文件的恢复；
- Agent Skill 自然语言入口与基础教学；
- Auto Git 自举和普通项目接入。
- Auto Git Skill、Git、Python、GitHub CLI 的 doctor 与安装策略；
- Git 提交身份、作用域和可选新仓库默认分支配置；
- 标准 Git Remote connect 与 GitHub remote create 计划；
- GitHub 认证检查与仓库创建适配器；
- 首次和后续 Push、non-fast-forward 阻断与 postflight；
- release profile、readiness、Release Commit、annotated Tag；
- branch Push、Tag Push、GitHub Release 分别审批与断点恢复。

### 6.2 Should Have（`0.1.0` 内尽量提供）

- 新手、标准、专家三档反馈；
- `history` 的紧凑记录列表；
- doctor 对 stale lock、运行时和项目配置给出明确诊断；
- 项目配置缺失时生成可复制的配置建议，但不自动覆盖文件。
- GitHub Release assets 上传与 checksum 摘要；
- 安装命令注册表的离线缓存和来源过期提醒。

### 6.3 Won't Have（本版本明确不做）

- PR、merge、force push；
- GitLab、Gitee 等非 GitHub Provider 的专用账号、仓库创建和 Release API；
- PyPI、npm、容器 Registry、应用商店等包发布；
- 自动 stash 或自动迁移脏改动；
- 自动解决 merge/rebase 冲突；
- 自动删除未知 branch、Worktree 或文件；
- 后台守护进程和全目录监控；
- 云端账号、凭证托管和遥测；
- ANK 运行时集成、独立 Auto Git CLI 或 MCP Server；
- 系统范围的 root/admin Auto Git 安装和单文件二进制；
- 自动安装未知 Linux 发行版或自行下载未经验证的第三方安装包。

## 7. 前提、约束与依赖

### 7.1 前提

- Agent 宿主已经能够发现和加载 Auto Git Skill；
- 本机能运行 Python 3.11+，或能先由 Skill 提供受支持平台的 Python 安装引导；
- Agent 能调用 Skill 自身的确定性 scripts 并展示输出；
- 用户可以对明确计划给出或拒绝审批；
- 项目回归命令可以用 program + argv 表达。

### 7.2 约束

- 使用标准 Git 仓库格式；
- Core 不调用模型 Provider；
- Core 不保存凭证和完整敏感 diff；
- 运行时采用 Python 3.11+ 标准库优先；
- Auto Git 运行时不依赖 ANK、Skill Engineering 或单一 Agent 宿主；
- 不使用 shell 拼接用户路径或自由文本；
- 用户安装对象只有 Auto Git Skill，不要求额外安装独立 pipx CLI；
- Commit、Remote、Push、Tag、Release 和恢复分别审批；
- GitHub 登录由官方浏览器流程和系统凭证库接管，Auto Git 不接收 Token；
- Release 不允许 Provider 隐式创建 Tag。

### 7.3 外部依赖

- Git 版本差异通过 capability 检测，不从开发机版本猜最低支持范围；
- 安装命令来自版本化平台注册表与官方来源，未知平台 fail closed；
- GitHub 仓库创建和 Release 依赖官方 GitHub CLI；已有 Remote 的 Push 只依赖标准 Git；
- 项目测试框架由项目自己定义，Auto Git 只编排受信命令；
- Git hooks 可能有外部副作用，Core 负责检测但不覆盖用户文件。

## 8. 端到端用户旅程

### 8.1 首次安装与环境准备

1. 用户从 GitHub 主源或 Gitee 镜像使用标准 Skills CLI/宿主 Skill 管理器安装，
   安装前明确 source、version、target host 和 project/global 范围。
2. 标准安装器完成安装后，由宿主证明 Auto Git Skill 可被发现和触发；GitHub/Gitee
   两源的版本、manifest 和关键文件 hash 必须一致。
3. Skill 先使用宿主允许的固定只读探测确认 Python；Python 3.11+ 可用后再调用
   bundled doctor script，读取 OS、架构、Python、PATH、Git 和 GitHub CLI，不进行
   系统写入。
4. 缺少 Git 或 GitHub CLI 时，Core 生成平台专属 install plan，显示官方来源、命令、
   管理员权限、下载/包来源和验证命令。
5. 用户批准对应 install plan 后才执行；系统密码、GUI 弹窗或浏览器登录由官方工具接管。
6. 安装完成后重新启动独立探测，验证 executable path、版本和 capability。
7. doctor 读取 Git 提交身份及来源；缺失时让用户选择当前项目或用户级作用域，预览后
   配置姓名、邮箱和可选默认分支。
8. 标准 Skill 安装器的无 Git 前置条件必须在 clean environment 实测；发现实际依赖
   Git 时使用宿主原生标准入口并如实说明，不创建 Auto Git 私有安装脚本。
8. GitHub 登录通过官方浏览器流程完成；Auto Git 只读取认证状态，不读取或保存 Token。

### 8.2 开始任务

1. 用户说“我要做一个功能”。
2. Skill 调用 inspect。
3. Core 返回分支、脏状态、Worktree、冲突和回归能力。
4. Skill 给出当前 checkout / 新分支 / Worktree 建议与理由。
5. 需要写入时生成 workspace plan。
6. 用户批准后 Apply，同一计划漂移则重新预览。

### 8.3 准备 Commit

1. 用户说“我改完了，准备提交”。
2. Skill 确认本任务文件范围。
3. Core 生成 Commit plan：文件、message、回归、风险、恢复。
4. 用户批准同一 plan id/hash。
5. Core 备份 index、精确 stage、验证范围、跑回归并 Commit。
6. Core postflight，生成 record。
7. Skill 报告本地 Commit 结果、当前 ahead/behind，并明确是否尚未 Push。

### 8.4 创建或连接远端

1. 用户选择“连接已有仓库”或“在 GitHub 创建仓库”。
2. Core 读取现有 remotes 并脱敏；GitHub Adapter 读取认证账号和目标 Owner 权限。
3. remote plan 展示 Provider、Owner、仓库名、可见性、目标 URL、remote name，以及
   是否为空仓库；默认可见性不从目录或聊天猜测。
4. 用户单独批准后创建仓库或添加 Remote；创建仓库时不把 `create + push` 合并执行。
5. postflight 重新读取 Remote，验证本地配置和 GitHub 仓库身份一致。

### 8.5 Push

1. Core 先 fetch 目标 Remote，读取 upstream、ahead/behind、目标 ref 和保护状态。
2. Push plan 展示将公开的 Commit 范围、Remote、branch、回归结果和失败影响。
3. 用户单独批准 plan id/hash 后，首次 Push 设置 upstream；后续 Push 使用已验证 upstream。
4. non-fast-forward、behind、认证失败、secret protection 或目标漂移立即阻断，不自动
   rebase、merge、force push 或绕过保护。
5. postflight 读取远端 ref OID，只有与批准的本地 OID 一致才报告 Push 成功。

### 8.6 Release

1. 用户提出“发布某版本”，Core 读取 release profile、当前版本、最近 Tag 和远端事实。
2. readiness 检查 clean 状态、允许分支、full regression、版本一致性、变更日志、构建
   命令和产物；任一缺失都只给修复建议。
3. Release plan 固定目标版本、Commit OID、Tag、notes、assets 和每个公开 checkpoint。
4. Release Commit、annotated Tag、branch Push、Tag Push 和 GitHub Release 分别请求批准。
5. GitHub Release 必须引用已在远端验证存在的 Tag，不允许 CLI 隐式建 Tag。
6. postflight 验证版本、远端 branch、远端 Tag、Release URL 和 assets 摘要一致。
7. 中断时保存 checkpoint；resume 先重读远端事实，只执行尚未成功且仍与计划一致的步骤。

### 8.7 失败与恢复

1. 回归、hook、Commit 或 postflight 失败。
2. Core 停止后续动作，恢复自己修改过的 index。
3. 若外部 hook 改了文件，保留现场并报告副作用。
4. 用户要求恢复时，Core 先根据 record 生成恢复计划。
5. 只有 ownership 和 fingerprint 仍成立时才执行；否则 explain-only。

## 9. 功能需求

| ID | 功能需求 | 优先级 | 对应 Story |
|---|---|---|---|
| FR-001 | 读取 Git/非 Git 目录机器事实，输出结构化 inspect | P0 | US-001 |
| FR-002 | 对非 Git 目录生成并执行 init 计划 | P0 | US-002 |
| FR-003 | 根据分支、脏状态、并行和风险推荐工作区 | P0 | US-003 |
| FR-004 | 保护既有脏改动，不自动 stash、覆盖或搬运 | P0 | US-004 |
| FR-005 | 生成不可变 plan，并在漂移或审批不匹配时阻断 | P0 | US-005 |
| FR-006 | 只 stage 明确批准的 literal paths | P0 | US-006 |
| FR-007 | 执行受信回归档位，失败时阻断 Commit | P0 | US-007 |
| FR-008 | 执行 Commit 并完成 postflight | P0 | US-008 |
| FR-009 | 保存脱敏 operation record 并支持 verify | P0 | US-009 |
| FR-010 | 根据 record 提供 ownership-aware recovery | P0 | US-010 |
| FR-011 | 用自然语言解释事实、策略、审批和恢复 | P0 | US-011 |
| FR-012 | 接入项目现有回归配置且不替换工具链 | P0 | US-012 |
| FR-013 | 支持 Auto Git 自举和普通项目可信验收 | P0 | US-013 |
| FR-014 | 检测 OS、Python、PATH、Git、GitHub CLI 和认证 capability | P0 | US-014 |
| FR-015 | 为受支持平台生成、执行并验证 Git/GitHub CLI 安装计划 | P0 | US-015 |
| FR-016 | 支持 Auto Git Skill 的无 Git 获取、宿主发现、升级、卸载与范围验证 | P0 | US-016 |
| FR-017 | 指导 GitHub 登录并证明 Core 不接触凭证 | P0 | US-017 |
| FR-018 | 创建 GitHub 仓库或连接标准 Git Remote，并完成 postflight | P0 | US-018 |
| FR-019 | 生成并执行首次 Push 计划，设置并验证 upstream | P0 | US-019 |
| FR-020 | 安全执行后续 Push，阻断 behind、漂移和 non-fast-forward | P0 | US-020 |
| FR-021 | 读取 release profile 并执行版本发布 readiness | P0 | US-021 |
| FR-022 | 分阶段执行 Release Commit、annotated Tag、Push 和 GitHub Release | P0 | US-022 |
| FR-023 | 对部分发布失败提供 checkpoint、verify、resume 与 explain-only | P0 | US-023 |
| FR-024 | 检查并经审批配置 Git 提交身份、作用域和可选默认分支 | P0 | US-024 |
| FR-025 | 提供中英 README、中文用户手册，并将受控发布副本同步到布丁 | P0 | US-025 |

## 10. 非功能需求

| ID | 类别 | 要求 |
|---|---|---|
| NFR-001 | 安全 | 不存在 `git add -A`、`git add .`、`reset --hard`、`clean -fdx` 执行路径 |
| NFR-002 | 确定性 | 相同事实与参数生成相同 canonical plan hash |
| NFR-003 | 隐私 | 不持久化完整 diff、文件内容、凭证、Cookie、私钥或带凭证 remote URL |
| NFR-004 | 可恢复 | 失败补偿只操作本次 operation 拥有且未漂移的资产 |
| NFR-005 | 可审计 | 每次 apply 保存 plan、approval assertion、pre/post facts、结果与 verification |
| NFR-006 | 跨平台 | 支持 Python 3.11–3.14；验证 macOS、Windows、Debian/Ubuntu、Fedora/RHEL |
| NFR-007 | 兼容 | 不要求重写 Git 历史、CI、hooks、测试框架或开发方式 |
| NFR-008 | 可解释 | 写入前显示动作、范围、风险、回归、审批与恢复 |
| NFR-009 | 并发 | per-repo lock 阻止两个写入操作同时执行 |
| NFR-010 | 失败封闭 | 漂移、配置不可信、回归失败或验证不足时默认停止 |
| NFR-011 | 可测试 | 所有 Git 集成测试只使用临时仓库，不触碰真实项目 |
| NFR-012 | 本地优先 | inspect、plan、Commit 和恢复可离线；只有安装下载和已批准远程动作需要网络 |
| NFR-013 | 供应链 | 安装计划只引用官方或明确标注的系统包来源，并记录来源与版本 |
| NFR-014 | 最小权限 | Auto Git Skill 安装必须显式选择 project/profile/global 范围；需要 admin/sudo 的依赖安装必须单独说明和批准 |
| NFR-015 | 凭证隔离 | 不通过 argv、plan、record、日志或 stdin 接收/保存 Token、密码和私钥 |
| NFR-016 | Provider 解耦 | GitHub Adapter 不进入 Git 状态、计划哈希和标准 Remote 核心模型 |
| NFR-017 | 远端验证 | Push/Tag/Release 成功必须以重新读取的远端事实为准，不只相信退出码 |
| NFR-018 | 发布幂等 | 相同 Release plan 重放不重复 Tag、Release 或 assets；冲突时 fail closed |
| NFR-019 | Skill 可发现性 | `0.1.0` 至少验证 Codex 与 Claude Code 的 discovery、正反触发和 bundled script 调用 |
| NFR-020 | 开发/运行隔离 | Skill Engineering 负责开发治理，但不得成为 Auto Git 的用户安装项或运行时 delegate |
| NFR-021 | 用户文档一致性 | 中英 README 的版本、能力、安装、边界和链接语义一致；仓库手册与布丁发布正文可校验同源 |

## 11. User Stories 与验收条件

### US-001：查看真实仓库状态

**优先级：** P0

**需求映射：** FR-001

**User Story**

作为使用 Agent 的用户，我希望系统先告诉我当前目录是否受 Git 管理、在哪个分支、
有哪些改动和风险，这样我可以基于真实状态决定下一步。

**验收条件**

- **US-001-AC01：非 Git 目录识别**
  - Given 当前目录及其父级不属于 Git 仓库；
  - When 用户要求“检查这个项目”；
  - Then 系统返回 `is_git_repo=false`，说明尚未初始化，并且不创建 `.git` 或其他文件。

- **US-001-AC02：Git 仓库事实**
  - Given 当前目录属于 Git 仓库；
  - When 系统执行 inspect；
  - Then 返回 repo root、branch/unborn/detached、HEAD、index、staged、unstaged、
    untracked、冲突、Worktree 和 upstream 等结构化事实。

- **US-001-AC03：只读保证**
  - Given 任意可读取仓库；
  - When 只执行 inspect；
  - Then HEAD、index、refs、工作区文件及 Git 状态在前后保持一致。

- **US-001-AC04：特殊路径**
  - Given 文件名含空格、Unicode、换行、pathspec 字符或以 `-` 开头；
  - When 系统解析 porcelain v2/NUL；
  - Then 每个路径被完整区分，不按可视行或空格错误拆分。

- **US-001-AC05：敏感 remote**
  - Given remote URL 可能带用户名、token 或其他凭证片段；
  - When inspect 输出人类文本或 JSON；
  - Then 只显示 remote 名称和脱敏 host，不持久化完整敏感 URL。

### US-002：把新目录纳入 Git

**优先级：** P0

**需求映射：** FR-002、FR-005

**User Story**

作为 Git 新手，我希望用一句“把这个项目纳入 Git 管理”完成安全初始化，这样我不必
记忆 `git init` 或默认分支参数。

**验收条件**

- **US-002-AC01：只生成计划**
  - Given 当前目录不是 Git 仓库；
  - When 用户提出初始化请求但尚未批准；
  - Then 系统只生成 init plan，展示目标目录、初始分支、风险和预期结果，不创建
    `.git`。

- **US-002-AC02：嵌套仓库保护**
  - Given 当前目录已经位于另一个 Git worktree 内；
  - When 用户请求初始化；
  - Then 系统明确报告嵌套风险并阻断，而不是静默创建嵌套仓库。

- **US-002-AC03：同计划执行**
  - Given 用户已看到 plan id/hash 且目录 fingerprint 未变化；
  - When 用户明确批准 init；
  - Then Core 只执行该 plan 中的初始化动作。

- **US-002-AC04：目录漂移**
  - Given plan 生成后目录内容或 `.git` 存在状态发生变化；
  - When Apply 旧 plan；
  - Then 系统返回 drift，要求重新预览，不继续初始化。

- **US-002-AC05：初始化验证**
  - Given `git init` 返回成功；
  - When postflight 执行；
  - Then 系统验证 repo root、初始分支和 Git 可读性，并保存 operation record。

- **US-002-AC06：不自动首提**
  - Given init 已成功；
  - When 用户没有单独批准 Commit；
  - Then 系统不 stage、不 Commit，也不创建 remote。

### US-003：选择当前分支、功能分支或 Worktree

**优先级：** P0

**需求映射：** FR-003

**User Story**

作为准备开始任务的用户，我希望系统根据真实状态推荐最合适的工作区，这样我既不会
污染主分支，也不会为每个小改动都承担 Worktree 的额外复杂度。

**验收条件**

- **US-003-AC01：功能分支继续工作**
  - Given 当前已在功能分支、改动单一且没有并行任务；
  - When 用户开始普通补丁或小功能；
  - Then 推荐继续当前 checkout，并解释无需额外 Worktree 的原因。

- **US-003-AC02：主分支功能开发**
  - Given 当前在 `main/master` 且工作区干净；
  - When 用户开始功能开发；
  - Then 推荐创建功能分支；未经批准不执行 branch 创建。

- **US-003-AC03：并行或高风险任务**
  - Given 存在并行任务、重构或高风险变更；
  - When 系统评估 workspace；
  - Then 优先推荐 Worktree，并展示 base、branch、path 和基线回归要求。

- **US-003-AC04：已有 linked worktree**
  - Given 当前已经位于 linked worktree；
  - When 系统评估隔离；
  - Then 不创建嵌套 Worktree，并报告当前 worktree identity。

- **US-003-AC05：detached HEAD**
  - Given 当前处于 detached HEAD；
  - When 用户准备进入写入任务；
  - Then 阻断 Commit 流程，先建议建立可追踪分支。

- **US-003-AC06：策略可解释**
  - Given 系统给出任一工作区建议；
  - When Skill 呈现结果；
  - Then 至少说明当前事实、推荐选择、未选方案和恢复/返回路径。

### US-004：保护脏工作区中的已有改动

**优先级：** P0

**需求映射：** FR-004

**User Story**

作为已经有未提交改动的用户，我希望开始新任务时现有文件不会被覆盖、清理或误带走，
这样我可以放心让 Agent 选择分支或 Worktree。

**验收条件**

- **US-004-AC01：全部改动属于当前任务**
  - Given 当前在主分支且所有脏改动都被用户确认属于当前任务；
  - When 创建功能分支计划获批；
  - Then 在当前 checkout 建分支并保留所有工作区文件内容。

- **US-004-AC02：存在无关改动**
  - Given 原 checkout 含与新任务无关的改动；
  - When 用户开始独立新任务；
  - Then 推荐从当前 HEAD 创建新 Worktree，原 checkout 的脏改动保持原位。

- **US-004-AC03：不自动搬运**
  - Given 任意脏工作区；
  - When 系统选择工作区策略；
  - Then 不自动 stash、不自动 apply patch、不自动把脏改动复制到 Worktree。

- **US-004-AC04：基线失败**
  - Given 新工作区的基线回归失败；
  - When workspace postflight 执行；
  - Then 报告失败并停止后续写入，不声称工作区已准备完成。

- **US-004-AC05：文件保护证据**
  - Given workspace 操作前已计算原改动 fingerprint；
  - When 操作完成或失败；
  - Then 原 checkout 中这些文件仍存在；若 hash 改变，系统报告异常而不是覆盖。

### US-005：批准一份不可漂移的计划

**优先级：** P0

**需求映射：** FR-005

**User Story**

作为需要把关的用户，我希望审批的是一份明确且不会被 Agent 偷换的计划，这样我的
“同意”只对我看到的动作生效。

**验收条件**

- **US-005-AC01：计划内容完整**
  - Given 任一写入请求；
  - When Core 生成 plan；
  - Then plan 包含动作、argv、文件范围、风险、回归、preconditions、postconditions、
    rollback summary、plan id 和 plan hash。

- **US-005-AC02：审批粒度**
  - Given 用户批准 workspace plan；
  - When Agent 后续要 Commit；
  - Then 必须生成新的 Commit plan，不能复用 workspace 审批。

- **US-005-AC03：计划防篡改**
  - Given plan JSON 的任一哈希字段外内容被修改；
  - When Apply；
  - Then 系统返回 plan hash 不一致，不执行任何 Git 写入。

- **US-005-AC04：仓库漂移**
  - Given plan 后 HEAD、index、status、selected path 或配置发生变化；
  - When Apply；
  - Then 系统拒绝旧 plan，并说明哪类 precondition 已变化。

- **US-005-AC05：审批缺失**
  - Given plan 有效但没有动作对应的 approval assertion；
  - When Apply；
  - Then 返回 `approval_missing`，不执行动作。

- **US-005-AC06：幂等重放**
  - Given 同一 plan 已成功并存在 verified record；
  - When 再次 Apply 且 postcondition 仍成立；
  - Then 返回原记录，不重复执行 Git 写入。

### US-006：只提交本任务文件

**优先级：** P0

**需求映射：** FR-006

**User Story**

作为工作区中可能有多组改动的用户，我希望 Auto Git 只 stage 我确认属于本任务的文件，
这样 Commit 不会混入其他工作、凭证或半成品。

**验收条件**

- **US-006-AC01：显式路径**
  - Given 用户准备 Commit；
  - When 生成 Commit plan；
  - Then 每个 selected path 都以 repo-relative literal path 明确列出。

- **US-006-AC02：禁止宽泛 staging**
  - Given 任意 Commit 流程；
  - When 检查计划和执行 argv；
  - Then 不存在 `git add -A`、`git add .` 或等价的全仓默认 staging。

- **US-006-AC03：范围外 staged 文件**
  - Given index 已包含 selected path 以外的 staged 文件；
  - When 生成或应用 Commit plan；
  - Then 阻断并列出范围外文件，不自动 unstage 用户已有内容。

- **US-006-AC04：删除与 rename**
  - Given selected path 包含删除或 rename；
  - When 精确 staging；
  - Then staged 结果保留正确变更类型，且新旧路径不会被误拆。

- **US-006-AC05：特殊字符路径**
  - Given selected path 含空格、Unicode、换行、glob/pathspec 字符或以 `-` 开头；
  - When staging；
  - Then 使用 NUL + literal pathspec 处理，staged set 与计划一致。

- **US-006-AC06：post-stage 验证**
  - Given Git staging 返回成功；
  - When Core 检查 index；
  - Then staged path set 必须与计划完全一致，否则恢复 apply 前 index 并阻断 Commit。

### US-007：运行可信的项目回归

**优先级：** P0

**需求映射：** FR-007、FR-012

**User Story**

作为项目维护者，我希望 Auto Git 运行项目已经认可的检查，而不是猜一条命令或相信
聊天里的“测过了”，这样 Commit 的质量门禁可复现。

**验收条件**

- **US-007-AC01：回归档位**
  - Given task kind 为功能、补丁或文档；
  - When 生成 Commit plan；
  - Then 分别要求 `full`、`quick`、`docs/integrity` 对应档位。

- **US-007-AC02：首次配置不自动信任**
  - Given `.auto-git.toml` 的 fingerprint 从未获批；
  - When 系统准备运行项目命令；
  - Then 展示完整 program + argv、cwd 和 timeout，等待用户建立本机信任。

- **US-007-AC03：配置漂移**
  - Given 已信任配置内容发生变化；
  - When 再次运行回归；
  - Then 原信任失效，系统要求重新预览和批准。

- **US-007-AC04：不使用自由 shell**
  - Given 项目配置声明回归；
  - When Core 解析配置；
  - Then 只接受 program + argv，不接受任意 shell command string。

- **US-007-AC05：失败阻断**
  - Given required command 返回非零、timeout、signal、executable missing 或配置不可信；
  - When Commit apply 执行；
  - Then Commit 被阻断，index 恢复到 apply 前状态。

- **US-007-AC06：无项目回归**
  - Given 功能任务没有 `full` profile；
  - When 用户准备 Commit；
  - Then 系统明确报告门禁缺失并阻断，不把内置 integrity 冒充完整项目测试。

- **US-007-AC07：不替换项目工具链**
  - Given 项目已有 pytest、npm、cargo、make 或自定义脚本；
  - When 接入 Auto Git；
  - Then Auto Git 调用现有入口，不重写测试脚本、CI 或 package 配置。

### US-008：安全完成 Commit

**优先级：** P0

**需求映射：** FR-008

**User Story**

作为完成工作的用户，我希望系统在我确认文件、message 和回归后安全 Commit，并证明
实际提交与计划一致，这样“提交成功”不是一句未经验证的话。

**验收条件**

- **US-008-AC01：Commit 预览**
  - Given selected paths 和 message 已确定；
  - When 生成 Commit plan；
  - Then 展示文件清单、Commit subject、required regression、风险和恢复入口。

- **US-008-AC02：index backup**
  - Given Commit plan 已获批且 preconditions 有效；
  - When staging 前；
  - Then Core 创建 operation-owned index backup，并记录 fingerprint。

- **US-008-AC03：Git hooks**
  - Given 仓库存在正常 Git hooks；
  - When 执行 Commit；
  - Then 默认正常运行 hooks，不使用 `--no-verify` 绕过。

- **US-008-AC04：成功 postflight**
  - Given `git commit` 返回成功；
  - When postflight 执行；
  - Then 验证 HEAD 变化、Commit OID、提交路径、message hash、status 和 hook 结果。

- **US-008-AC05：Commit 失败**
  - Given `git commit` 返回非零且未创建目标 Commit；
  - When failure compensation 执行；
  - Then 恢复 apply 前 index，不删除或覆盖工作区文件。

- **US-008-AC06：hook 外部副作用**
  - Given hook 修改了工作区文件；
  - When postflight 检测到 fingerprint 变化；
  - Then 保留修改，标记 `external_side_effect_detected`，不自动用旧内容覆盖。

- **US-008-AC07：Commit 与 Push 分离**
  - Given Commit 已成功；
  - When Skill 汇报结果；
  - Then 明确说明 Commit 当前仅在本地；除非已有另一个获批 Push plan，否则不执行
    Push、PR 或任何远程动作。

### US-009：验证并审计操作记录

**优先级：** P0

**需求映射：** FR-009

**User Story**

作为用户或维护者，我希望之后能查看 Auto Git 实际执行了什么并重新验证结果，这样
我不需要依赖 Agent 的聊天记忆。

**验收条件**

- **US-009-AC01：记录完整性**
  - Given 任一 apply 已开始；
  - When operation 结束；
  - Then record 包含 plan id/hash、审批断言、pre/post fingerprint、动作、退出码、
    回归摘要、ownership、verification 和最终状态。

- **US-009-AC02：成功验证**
  - Given record 状态为 verified 且仓库 postcondition 未变化；
  - When 用户执行 verify；
  - Then 返回 verified，并列出通过的结构化 checks。

- **US-009-AC03：记录后漂移**
  - Given record 后 HEAD、ref、Worktree 或 owned asset 发生变化；
  - When verify；
  - Then 返回 drifted，指出不再成立的 check，不修改仓库。

- **US-009-AC04：隐私**
  - Given operation 涉及 diff、remote、测试输出或 message；
  - When 保存 record；
  - Then 不保存完整 diff、文件内容、完整 stdout/stderr 或敏感 remote URL。

- **US-009-AC05：历史列表（P1）**
  - Given 当前 repo 有多条 records；
  - When 用户查看 history；
  - Then 按时间返回 operation、状态、plan id、Commit OID 和 recovery availability，
    不把其他 repo 的记录混入。

### US-010：失败后安全恢复

**优先级：** P0

**需求映射：** FR-010

**User Story**

作为遇到失败或误提交的用户，我希望 Auto Git 先确认哪些资产由它创建，再提供不丢
文件的恢复计划，这样我不会因为恢复动作造成第二次事故。

**验收条件**

- **US-010-AC01：恢复先预览**
  - Given 用户指定 operation record；
  - When 请求恢复；
  - Then 系统先 verify record 并生成 recover plan，不直接修改 Git。

- **US-010-AC02：恢复 index**
  - Given Commit 前失败且 index backup 仍与 record ownership 匹配；
  - When `restore-index` 获批；
  - Then 恢复到 apply 前 index，工作区文件保持现状。

- **US-010-AC03：soft uncommit**
  - Given HEAD 仍是 Auto Git 记录的最新本地 Commit，且该 Commit 不可从本地
    remote-tracking ref 到达；
  - When `soft-uncommit` 获批；
  - Then 先创建 backup ref，再移动 HEAD 到 parent，并保留文件与 staged 内容。

- **US-010-AC04：远程或事实不足**
  - Given Commit 可能已公开、remote facts 不足或 HEAD 已漂移；
  - When 请求 soft uncommit；
  - Then 系统拒绝自动执行，返回 explain-only。

- **US-010-AC05：Worktree ownership**
  - Given Worktree 由该 operation 创建且仍干净、未漂移；
  - When 用户单独批准删除恢复；
  - Then 只删除该 Worktree；branch 删除不被顺带执行。

- **US-010-AC06：未知资产**
  - Given ref、Worktree、index 或文件无法证明由 record 创建；
  - When 请求恢复；
  - Then 不修改资产，只解释风险和人工检查路径。

- **US-010-AC07：危险命令禁止**
  - Given 任意恢复请求；
  - When Core 生成执行动作；
  - Then 不生成 `reset --hard`、`clean -fdx`、force push 或未知文件删除。

### US-011：用自然语言理解 Git 决策

**优先级：** P0

**需求映射：** FR-011

**User Story**

作为不想背 Git 命令的用户，我希望 Agent 用适合我的层级解释当前状态、推荐策略和
审批影响，这样我既能完成任务，也能逐步学会把关。

**验收条件**

- **US-011-AC01：新手四问**
  - Given feedback level 为新手；
  - When Skill 呈现任一关键步骤；
  - Then 回答“现在在哪里、为什么这样选、将发生什么、怎样恢复”。

- **US-011-AC02：标准模式（P1）**
  - Given feedback level 为标准；
  - When Skill 呈现结果；
  - Then 先给结论，再给文件范围、回归、审批点和下一步。

- **US-011-AC03：专家模式（P1）**
  - Given feedback level 为专家；
  - When Skill 呈现结果；
  - Then 提供紧凑 facts、plan hash、pre/post 和 JSON 入口，不省略安全门禁。

- **US-011-AC04：阻断解释**
  - Given drift、回归失败、权限不足或恢复不安全；
  - When Skill 报告阻断；
  - Then 说明真实原因、未执行的动作和安全下一步，不伪造成功。

- **US-011-AC05：教学不降级安全**
  - Given 用户切换任一反馈层级；
  - When 执行相同写入意图；
  - Then plan、审批、回归、漂移和恢复门禁完全一致。

- **US-011-AC06：不要求记命令**
  - Given 普通用户完成最小可信场景；
  - When 通过自然语言与 Skill 交互；
  - Then 用户不需要手工输入 Git 命令即可走到审批和结果验证。

### US-012：让现有项目接入自己的回归规则

**优先级：** P0

**需求映射：** FR-007、FR-012

**User Story**

作为现有项目维护者，我希望用最小配置告诉 Auto Git 哪些命令属于 quick/full/docs，
这样项目无需更换测试框架或开发方式。

**验收条件**

- **US-012-AC01：无配置只读接入**
  - Given 现有项目没有 `.auto-git.toml`；
  - When 首次运行 inspect/doctor；
  - Then 只读盘点仍可使用，并说明只有内置 integrity，功能 Commit 尚缺 full profile。

- **US-012-AC02：读取现有入口**
  - Given 配置以 program + argv 声明已有测试脚本；
  - When 用户批准配置 fingerprint；
  - Then Core 调用原入口，不修改 package、CI、Makefile 或脚本内容。

- **US-012-AC03：配置建议不覆盖**
  - Given 项目缺回归配置；
  - When doctor 生成建议；
  - Then 只输出可复制的建议内容，不修改项目文件；用户已有配置保持原样。

- **US-012-AC04：非敏感配置**
  - Given 项目配置准备进入仓库；
  - When Core 校验；
  - Then 配置只允许命令、档位、timeout 和项目策略，不允许 token、Cookie、密码或
    私钥。

- **US-012-AC05：兼容现有 Git**
  - Given 项目已有历史、hooks、分支约定和 CI；
  - When 接入 Auto Git；
  - Then 不重写历史、不替换 hooks、不要求迁移默认分支或 Provider。

### US-013：证明 Auto Git 可以可信自举和跨项目使用

**优先级：** P0

**需求映射：** FR-013

**User Story**

作为 Auto Git 的产品负责人，我希望它既能管理自身，也能在一个普通项目完成相同
闭环，这样可以证明它不是只对自己的仓库特制。

**验收条件**

- **US-013-AC01：临时仓库测试**
  - Given 自动化测试运行；
  - When 执行所有破坏性、失败和特殊路径 fixture；
  - Then 只使用临时仓库，不读取或修改用户真实项目。

- **US-013-AC02：Auto Git 自举**
  - Given Auto Git 的实现、配置和回归已准备；
  - When 使用 Auto Git 自身生成 Commit plan 并经用户批准执行；
  - Then 精确 staging、回归、Commit、postflight 和 record 全部通过。

- **US-013-AC03：普通项目接入**
  - Given 一个非 Auto Git 本地项目；
  - When 使用最小配置完成 inspect、workspace、regression 和 Commit；
  - Then 保留原历史、测试、hooks 和开发方式，并生成可验证 record。

- **US-013-AC04：十五个可信场景**
  - Given Roadmap 中 15 个最小可信场景；
  - When 发布验收执行；
  - Then 每个场景都有命令、fixture、期望结果和实际证据。

- **US-013-AC05：零到 Release 自举边界**
  - Given `0.1.0` 本地与远端验收能力已经准备；
  - When Auto Git 使用自身完成零到 Release 自举；
  - Then install、Commit、remote、Push、tag 和 Release 分别使用独立计划与审批记录，
    任一后续动作未获批准时停在最近一个已验证 checkpoint。

### US-014：在操作前诊断电脑环境

**优先级：** P0

**需求映射：** FR-014

**User Story**

作为不知道电脑是否装好 Git 的用户，我希望 Auto Git 先检查操作系统、Python、PATH、
Git、GitHub CLI 和登录状态，这样我能看到缺什么，而不是在一串报错后猜原因。

**验收条件**

- **US-014-AC01：只读环境探测**
  - Given 用户首次运行 doctor；
  - When Core 探测环境；
  - Then 返回 OS、架构、Python、PATH、Git、GitHub CLI 和 capability，不安装或修改任何组件。

- **US-014-AC02：Git 缺失**
  - Given PATH 中没有可执行 Git；
  - When doctor 完成；
  - Then 返回 `git.status=missing`、受支持的平台安装策略和下一步 plan 入口，不把
    “command not found”包装成仓库错误。

- **US-014-AC03：版本或 capability 不足**
  - Given Git 存在但缺少 0.1.0 必需 capability；
  - When doctor 检查；
  - Then 列出通过和缺失的 capability，建议升级，不根据单一版本字符串猜测可用性。

- **US-014-AC04：多版本与 PATH 冲突**
  - Given 系统存在多个 Git、Python 或 GitHub CLI；
  - When doctor 解析实际 executable；
  - Then 显示本次将使用的绝对路径与版本，并标记路径优先级冲突。

- **US-014-AC05：未知平台**
  - Given OS/发行版不在受支持平台注册表；
  - When doctor 完成；
  - Then 返回 explain-only 和官方入口，不生成或执行猜测的安装命令。

- **US-014-AC06：机器可读结果**
  - Given Agent 调用 `doctor --json`；
  - When 输出完成；
  - Then 使用稳定 schema 区分 `ready`、`missing`、`outdated`、`conflict`、
    `auth_required` 和 `unsupported`。

### US-015：在批准后安装 Git 与 GitHub CLI

**优先级：** P0

**需求映射：** FR-015

**User Story**

作为不会安装开发工具的用户，我希望系统给出适合当前操作系统、来自官方来源的安装
计划，并在我批准后执行和验证，这样我不需要复制来路不明的命令。

**验收条件**

- **US-015-AC01：平台专属安装计划**
  - Given doctor 判定 Git 或 GitHub CLI 缺失；
  - When 用户请求安装；
  - Then plan 固定目标组件、官方/系统包来源、program + argv、权限需求、预期版本
    范围和验证命令。

- **US-015-AC02：管理员权限透明**
  - Given 安装需要 macOS GUI、Windows UAC 或 Linux sudo；
  - When 展示 plan；
  - Then 明确说明会出现的系统交互；Auto Git 不收集、传递或记录密码。

- **US-015-AC03：审批与漂移**
  - Given install plan 已生成；
  - When OS、包管理器、源、目标组件或 plan hash 变化；
  - Then 旧审批失效并要求重新预览。

- **US-015-AC04：安装后独立验证**
  - Given 官方安装器返回成功；
  - When postflight 执行；
  - Then 重新解析 PATH、executable、版本和 capability；未通过时不报告安装成功。

- **US-015-AC05：部分安装或需重启终端**
  - Given 组件已安装但当前进程 PATH 尚未刷新；
  - When postflight 无法找到命令；
  - Then 标记 `restart_shell_required`，给出重新打开终端后继续验证的入口，不重复安装。

- **US-015-AC06：下载或源失败**
  - Given 网络、包源、签名或系统安装失败；
  - When apply 结束；
  - Then 保留原环境，记录脱敏错误与官方人工安装入口，不切换到未知第三方镜像。

### US-016：安装、发现、升级和卸载 Auto Git Skill

**优先级：** P0

**需求映射：** FR-016

**User Story**

作为普通用户，我希望 Auto Git 作为一个 Skill 被清楚地安装、发现、升级和卸载，
并能从 GitHub 主源或 Gitee 镜像使用标准 Skill 安装方式获取，这样我不需要先安装
第二个 Auto Git 程序，也不会留下不知道如何清理的内容。

**验收条件**

- **US-016-AC01：安装对象唯一**
  - Given 用户准备安装 Auto Git；
  - When 展示安装计划；
  - Then 明确安装对象是 Auto Git Skill，显示来源、版本、目标宿主和
    project/profile/global 范围，不要求额外安装独立 Auto Git CLI。

- **US-016-AC02：无 Git 获取路径**
  - Given 用户电脑尚未安装 Git；
  - When 用户获取 Auto Git Skill；
  - Then 明确当前标准仓库型 Skills CLI 需要 Git；由已存在的宿主 Agent 先展示
    系统官方/受信任包管理器的 Git 安装计划，用户批准并通过 `git --version`、PATH
    复验后，再使用标准 Skills CLI 安装 Auto Git；不声称尚未安装的 Skill 能先运行。

- **US-016-AC03：宿主发现验证**
  - Given Skill 文件已经写入目标范围；
  - When 安装 postflight 执行；
  - Then 目标 Agent 宿主能够发现 `auto-git`、读取有效 `SKILL.md` 和版本信息，并能
    命中一条正触发示例；仅“文件存在”不能报告安装成功。

- **US-016-AC04：脚本运行时验证**
  - Given Auto Git Skill 已被宿主发现；
  - When 执行首次 doctor；
  - Then 分别报告 Skill 就绪状态和 bundled scripts 所需 Python capability；Python
    缺失时提供受支持平台的官方安装引导，不把 Skill 安装失败与脚本运行时缺失混为一谈。

- **US-016-AC05：升级**
  - Given Auto Git Skill 已安装且存在新版本；
  - When 用户批准升级计划；
  - Then 显示 from/to 版本、作用范围、文件 diff 和兼容影响；升级后重新验证宿主发现、
    contract、scripts 与配置兼容，失败时恢复原版本或明确报告无法恢复的原因。

- **US-016-AC06：卸载**
  - Given 用户明确批准从指定范围卸载 Auto Git Skill；
  - When 卸载执行；
  - Then 只移除该范围内由安装记录拥有的 Auto Git Skill 文件；目标项目、Git 历史和
    本地 operation records 默认保留，并单独解释可选清理范围。

- **US-016-AC07：GitHub/Gitee 双安装源一致**
  - Given GitHub 主仓库与 Gitee 镜像声明同一 Auto Git 版本；
  - When 分别通过 GitHub 简写和 Gitee 完整 Git URL 使用标准 Skill 安装器安装；
  - Then 两次安装得到相同 Skill 版本、manifest 与关键文件 hash，且不需要
    `install.sh`、`install.ps1` 或独立 Auto Git CLI。

- **US-016-AC08：双远程发行可证明**
  - Given Auto Git 准备发布一个 Commit 或 annotated Tag；
  - When GitHub 与 Gitee Push 分别完成；
  - Then 只有两个远端 branch OID 与本地 HEAD 一致，并且同步 Tag 的 target Commit
    一致时，才能报告双远程发布成功；任一远程失败时生成可恢复 checkpoint。

### US-017：安全完成 GitHub 登录

**优先级：** P0

**需求映射：** FR-017

**User Story**

作为需要连接 GitHub 的用户，我希望 Auto Git 引导官方登录并告诉我当前账号与协议，
这样我不用把 Token 发给 Agent，也不会登录错账号。

**验收条件**

- **US-017-AC01：认证状态检查**
  - Given GitHub CLI 已安装；
  - When doctor 检查 GitHub；
  - Then 只返回 hostname、登录账号、Git protocol 和认证是否有效，不输出 Token。

- **US-017-AC02：浏览器登录**
  - Given 用户尚未认证并批准启动登录；
  - When GitHub Adapter 调用官方登录流程；
  - Then 默认使用浏览器认证，凭证由 GitHub CLI 与系统凭证库处理。

- **US-017-AC03：凭证降级风险**
  - Given GitHub CLI 无法使用系统凭证库；
  - When 登录流程可能降级到明文文件存储；
  - Then Auto Git 在继续前明确警告存储位置与风险，并要求单独确认。

- **US-017-AC04：账号确认**
  - Given 登录成功；
  - When 用户准备创建仓库或 Release；
  - Then plan 显示已验证账号和目标 Owner；账号变化使旧 plan 漂移。

- **US-017-AC05：认证失败或权限不足**
  - Given 登录过期、host 不符或 Owner 权限不足；
  - When remote/release plan 生成；
  - Then 阻断公开动作并指向重新登录或切换账号，不请求用户粘贴 Token。

- **US-017-AC06：尚无 GitHub 账号**
  - Given 用户没有 GitHub 账号；
  - When 进入 GitHub Remote 引导；
  - Then 解释账号、验证邮箱、公开/私有仓库和 2FA 的作用，打开官方注册入口；Auto Git
    不代填资料、不创建账号，也允许用户改为连接其他标准 Git Remote。

### US-018：创建或连接正确的远端仓库

**优先级：** P0

**需求映射：** FR-018

**User Story**

作为第一次使用远端仓库的用户，我希望系统帮助我创建 GitHub 仓库或连接已有仓库，
并清楚显示账号、可见性和 URL，这样不会把项目传到错误位置。

**验收条件**

- **US-018-AC01：连接已有 Remote**
  - Given 用户提供已有 HTTPS 或 SSH Remote URL；
  - When 生成 connect plan；
  - Then 校验 URL 结构、remote name 和重复项，脱敏显示 host/owner/repo，不访问或保存
    URL 中的凭证。

- **US-018-AC02：创建 GitHub 仓库**
  - Given GitHub 账号、Owner 和名称已确认；
  - When 生成 create plan；
  - Then 必须显式包含 public/private/internal 可见性；未选择时阻断，不使用猜测默认值。

- **US-018-AC03：创建与 Push 分离**
  - Given GitHub 仓库创建计划已批准；
  - When apply 创建远端仓库；
  - Then 只创建仓库并配置获批 Remote，不使用隐式 Push 选项。

- **US-018-AC04：远端非空**
  - Given 目标远端已有默认分支或 Commit；
  - When postflight/fetch 检测到历史；
  - Then 标记 `remote_non_empty`，在比较历史前不生成首次 Push 计划。

- **US-018-AC05：Remote 名称冲突**
  - Given 本地已存在同名 Remote 且 URL 不同；
  - When 请求 connect/create；
  - Then 显示现有与目标身份，阻断覆盖；修改 Remote 需独立 plan。

- **US-018-AC06：跨 Provider 标准兼容**
  - Given 用户连接 GitLab、Gitee 或自托管标准 Git URL；
  - When connect plan 获批；
  - Then 可配置和验证标准 Remote；不声称支持对应 Provider 的仓库创建或 Release API。

### US-019：安全完成第一次 Push

**优先级：** P0

**需求映射：** FR-019

**User Story**

作为完成第一次本地 Commit 的用户，我希望在看到要上传的 Commit、目标仓库和分支后
批准第一次 Push，这样本地成果能安全同步并建立正确 upstream。

**验收条件**

- **US-019-AC01：Push 前 fetch 与身份检查**
  - Given Remote 已配置；
  - When 生成首次 Push plan；
  - Then 先 fetch 并验证 remote identity、目标 branch、远端是否为空和认证状态。

- **US-019-AC02：公开范围预览**
  - Given 本地分支有待 Push Commit；
  - When 展示 plan；
  - Then 列出目标 remote/ref、Commit 数、起止 OID、subject 摘要、回归结果和是否设置 upstream。

- **US-019-AC03：独立审批**
  - Given 用户只批准了 Commit 或 remote create；
  - When 系统准备 Push；
  - Then 不复用旧批准，必须取得 Push plan id/hash 的单独审批。

- **US-019-AC04：首次 upstream**
  - Given 目标远端分支不存在且 plan 获批；
  - When Push 成功；
  - Then 设置并验证 upstream，且远端 ref OID 等于获批本地 OID。

- **US-019-AC05：Push 保护或认证阻断**
  - Given 远端拒绝 Push、secret protection 命中或认证失效；
  - When apply 返回失败；
  - Then 不绕过保护、不 force push，报告远端原因和安全修复入口。

- **US-019-AC06：网络结果不确定**
  - Given 客户端超时或连接中断，无法仅凭退出码判断 Push 是否成功；
  - When 恢复网络后 verify；
  - Then 读取远端 ref 决定 `verified`、`not_applied` 或 `unknown`，不盲目重复 Push。

### US-020：安全完成后续 Push

**优先级：** P0

**需求映射：** FR-020

**User Story**

作为持续开发的用户，我希望每次 Push 前系统确认本地与远端没有产生我不知道的分叉，
这样不会覆盖远端工作或误把旧计划推上去。

**验收条件**

- **US-020-AC01：ahead/behind**
  - Given 分支已有 upstream；
  - When 生成 Push plan；
  - Then fetch 后返回 ahead、behind、diverged 和目标远端 OID。

- **US-020-AC02：纯 ahead**
  - Given 本地 ahead 大于零、behind 为零且回归有效；
  - When plan 获批；
  - Then 只 Push 计划中的当前 branch 到已验证 upstream。

- **US-020-AC03：behind 或 diverged**
  - Given behind 大于零或历史分叉；
  - When 用户请求 Push；
  - Then 阻断并解释 fetch 后事实；不自动 merge、rebase、pull 或 force push。

- **US-020-AC04：无待 Push 内容**
  - Given 本地与远端 OID 相同；
  - When 用户请求 Push；
  - Then 返回 already-synced，不创建无意义写入 operation。

- **US-020-AC05：计划后 Remote 漂移**
  - Given Push plan 已批准；
  - When apply 前远端 ref、URL、upstream、HEAD 或回归 fingerprint 变化；
  - Then 旧 plan 失效，要求重新 fetch 和预览。

- **US-020-AC06：禁止强推**
  - Given 任意 Push 请求；
  - When Core 生成动作；
  - Then 0.1.0 不生成 `--force`、`--force-with-lease` 或 ref 删除语法。

### US-021：判断项目是否已经可以 Release

**优先级：** P0

**需求映射：** FR-021

**User Story**

作为准备发布版本的维护者，我希望系统先检查版本号、变更日志、测试、构建、Tag 和
远端状态，这样不完整的版本不会被公开。

**验收条件**

- **US-021-AC01：release profile**
  - Given 项目准备启用 Release；
  - When doctor 读取 `.auto-git.toml`；
  - Then 配置明确版本来源、允许分支、full regression、构建 argv、产物规则、Tag
    模板和 Release notes 来源。

- **US-021-AC02：缺失配置**
  - Given 项目没有足够的 release profile；
  - When 用户请求 Release；
  - Then 只生成配置建议与缺失项，不猜版本文件、构建命令或产物。

- **US-021-AC03：版本一致性**
  - Given 用户指定目标版本；
  - When readiness 执行；
  - Then 验证版本格式、当前版本、目标版本、Tag 模板和变更日志标题一致。

- **US-021-AC04：发布前状态**
  - Given 工作区脏、分支不允许、upstream behind/diverged 或存在同名本地/远端 Tag；
  - When readiness 执行；
  - Then 阻断并逐项说明，不修改文件或 Tag。

- **US-021-AC05：回归与构建**
  - Given 版本与仓库状态满足；
  - When readiness 执行 full regression 和构建；
  - Then 任何失败、timeout、未知命令或产物缺失均阻断 Release plan。

- **US-021-AC06：readiness 只读结果**
  - Given 所有检查通过；
  - When readiness 完成；
  - Then 返回目标版本、将修改的版本/变更日志文件、预期 Tag、notes、assets 与
    checkpoint 清单，不创建 Commit、Tag 或远端资源。

### US-022：分阶段创建并发布版本

**优先级：** P0

**需求映射：** FR-022

**User Story**

作为批准发布的维护者，我希望 Auto Git 按可见步骤创建 Release Commit、Tag、Push
和 GitHub Release，并验证每一步，这样版本历史和公开页面保持一致。

**验收条件**

- **US-022-AC01：不可变 Release plan**
  - Given readiness 已通过；
  - When 生成 Release plan；
  - Then 固定目标版本、文件、Commit message、Commit OID 前置条件、annotated Tag、
    notes hash、assets hash、Remote 和每个独立审批类。

- **US-022-AC02：Release Commit**
  - Given 版本/变更日志需要修改；
  - When 对应 plan 获批；
  - Then 只修改和 stage 配置声明的文件，跑 full regression，创建并验证 Release Commit。

- **US-022-AC03：annotated Tag**
  - Given Release Commit 已验证且同名 Tag 不存在；
  - When Tag plan 获批；
  - Then 在精确 Commit OID 创建 annotated Tag，并验证 annotation 与计划 hash。

- **US-022-AC04：branch 与 Tag 分别 Push**
  - Given 本地 Release Commit 和 Tag 已存在；
  - When 用户依次批准 Push；
  - Then branch Push 与单个 Tag Push 是两个记录；不使用 `--tags` 批量上传未知 Tag。

- **US-022-AC05：GitHub Release**
  - Given 远端 Tag 已验证存在；
  - When GitHub Release plan 获批；
  - Then 通过 GitHub Adapter 创建引用该 Tag 的 Release，并启用“Tag 不存在则失败”的
    语义，不允许 Provider 隐式建 Tag。

- **US-022-AC06：Release postflight**
  - Given GitHub CLI 返回成功；
  - When postflight 执行；
  - Then 验证 Release URL、Tag、target OID、title、draft/prerelease 状态和 assets 摘要，
    全部一致才报告发布成功。

- **US-022-AC07：不包含包发布**
  - Given GitHub Release 已完成；
  - When Skill 汇报结果；
  - Then 明确区分 GitHub Release 与 PyPI/npm/容器 Registry 发布；0.1.0 不声称后者已完成。

### US-023：发布中断后安全继续

**优先级：** P0

**需求映射：** FR-023

**User Story**

作为发布到一半遇到网络或权限问题的用户，我希望系统告诉我哪些步骤已经公开、哪些
尚未完成，并从验证后的 checkpoint 继续，这样不会重复 Tag 或创建重复 Release。

**验收条件**

- **US-023-AC01：checkpoint 记录**
  - Given Release operation 已开始；
  - When 每个 Commit、Tag、Push 或 Release 步骤结束；
  - Then 记录 planned、applied、verified、failed 或 unknown 状态和对应本地/远端 OID。

- **US-023-AC02：resume 前复验**
  - Given 存在中断 operation；
  - When 用户请求 resume；
  - Then 重新读取本地 HEAD、Remote branch、Remote Tag 和 GitHub Release，不只读取旧 record。

- **US-023-AC03：安全跳过已完成步骤**
  - Given 远端事实证明某 checkpoint 已与 plan 一致；
  - When resume plan 生成；
  - Then 标记该步骤 already-verified，不重复 Push、Tag 或创建 Release。

- **US-023-AC04：同名资源冲突**
  - Given 同名 Tag 或 Release 已存在但 OID、notes 或 assets 与 plan 不一致；
  - When resume；
  - Then fail closed 并 explain-only，不删除、不覆盖、不改写公开资源。

- **US-023-AC05：公开动作不自动回滚**
  - Given branch 或 Tag 已成功 Push，但后续 Release 失败；
  - When 系统处理失败；
  - Then 保留已公开事实，提供修复/继续方案，不 force push、不删除远端 Tag。

- **US-023-AC06：最终验证**
  - Given 所有 checkpoint 已完成；
  - When 用户请求 verify；
  - Then 版本来源、Release Commit、远端 branch、annotated Tag、Release 和 assets 全部一致，
    record 状态才变为 verified。

### US-024：完成第一次 Git 身份配置

**优先级：** P0

**需求映射：** FR-024

**User Story**

作为刚安装 Git 的用户，我希望系统检查并指导配置提交姓名、邮箱和作用域，这样第一
次 Commit 不会因身份缺失失败，也不会把工作身份误用到所有项目。

**验收条件**

- **US-024-AC01：读取有效身份与来源**
  - Given Git 已安装；
  - When doctor 检查首次配置；
  - Then 返回有效 `user.name`、脱敏邮箱、配置来源和作用域，不修改配置。

- **US-024-AC02：身份缺失阻断 Commit**
  - Given 当前仓库没有有效姓名或邮箱；
  - When 用户生成 Commit plan；
  - Then 阻断并进入 Git identity 配置流程，不伪造默认身份。

- **US-024-AC03：用户选择作用域**
  - Given 用户准备配置身份；
  - When 生成 config plan；
  - Then 明确选择 `local` 当前仓库或 `global` 当前系统用户；不默认写 system scope。

- **US-024-AC04：身份值必须确认**
  - Given 系统可从 GitHub 账号或 OS 推测姓名/邮箱；
  - When 展示建议；
  - Then 只作为建议，用户必须确认实际姓名和邮箱；敏感值不进入长期 operation record。

- **US-024-AC05：可选默认分支**
  - Given Git capability 支持 `init.defaultBranch`；
  - When 用户选择新仓库默认分支；
  - Then config plan 可独立包含 `main` 或用户选择值；不改已有仓库分支。

- **US-024-AC06：配置后验证**
  - Given config plan 已批准并执行；
  - When postflight 重新读取配置；
  - Then 有效值、来源和作用域与计划一致；不一致时不报告配置成功。

### US-025：通过双语入口和用户手册完成基本操作

**优先级：** P0

**需求映射：** FR-025

**User Story**

作为第一次接触 Auto Git 的普通用户，我希望从中文或英文 README 快速理解产品，
并通过一份完全从用户视角编写的中文手册完成安装、首次检查、Commit、远程仓库、
Push、Release、恢复、更新和卸载，这样我不需要阅读 PRD、ADR、源码或开发者测试文档。

**验收条件**

- **US-025-AC01：README 中英双版**
  - Given 用户打开 Auto Git 仓库；
  - When 进入 `README.md` 或 `README.en.md`；
  - Then 中文版与英文版顶部均提供明确语言切换，且产品定位、版本、能力、安装方式、
    安全边界、支持宿主、用户手册和问题反馈入口语义一致。

- **US-025-AC02：标准双源安装说明**
  - Given 用户选择安装 Auto Git；
  - When 阅读任一语言 README；
  - Then 能看到 GitHub 主源和 Gitee 镜像的标准 Skill 安装命令，以及 project/global、
    Codex/Claude Code 宿主参数、升级和卸载的用途、参数与影响；不出现
    `install.sh`、`install.ps1` 或必须安装 Skill Engineering 的表述。

- **US-025-AC03：纯用户视角手册**
  - Given 用户打开 `docs/knowledge/users/guides/auto-git-user-manual.zh-CN.md`；
  - When 按顺序阅读；
  - Then 内容不要求先理解 Skill Engineering、TDD、ADR、JSON schema 或内部架构，
    而是使用“你可以说什么、Auto Git 会做什么、何时需要确认、如何判断成功”的语言。

- **US-025-AC04：基本操作闭环**
  - Given 用户从零开始；
  - When 按手册操作；
  - Then 手册依次覆盖安装 Skill、首次触发、doctor、Git/Python/gh 准备、Git identity、
    init/inspect、准备 Commit、连接或创建 Remote、首次/后续 Push、Release、失败恢复、
    更新和卸载，并为每一步给出预期结果。

- **US-025-AC05：自然语言优先且命令可教学**
  - Given 用户不记忆 Git 命令；
  - When 手册展示操作；
  - Then 首先给出可直接复制给 Agent 的自然语言示例；确需展示命令时逐条解释用途、
    参数和影响，不把命令列表当成唯一教程。

- **US-025-AC06：安全与诚实边界**
  - Given 手册描述 Commit、Push、Tag、Release、Global 安装或系统依赖安装；
  - When 用户准备执行；
  - Then 明确对应审批、凭证隔离、测试前置、恢复路径和当前平台验证范围，不承诺
    “安装后所有 Agent 会自动提交”，不把训练营写成 Auto Git 产品功能。

- **US-025-AC07：布丁发布副本隔离**
  - Given 仓库中文用户手册通过内容验收；
  - When 准备同步布丁；
  - Then 在
    `/Users/aim5/Documents/OB/_OB工程/publications/auto-git/Auto Git 用户手册.md`
    创建面向用户的发布副本，只加入布丁所需公开 frontmatter；`pudding_id`、后台 URL、
    同步时间等环境元数据只允许留在 OB 副本，不写入 GitHub/Gitee 仓库。

- **US-025-AC08：布丁预览、同步与 postflight**
  - Given OB 发布副本已准备；
  - When 执行布丁发布；
  - Then 先运行 `pudding sync <file>` dry-run 并检查标题、类型和正文字数；用户已确认
    同步内容后才运行同一目标的 `--apply`，随后用 `pudding status <file>` 验证并记录
    真实 `case_id`、后台 URL 和 draft/published 状态；只有状态为 published 时才要求
    公开 URL，不编造 `pudding_id` 或 URL。

- **US-025-AC09：仓库与布丁正文同源**
  - Given 仓库手册或 OB 发布副本发生修改；
  - When 执行文档一致性检查；
  - Then 去除平台专属 frontmatter 后，两份用户正文和声明的 Auto Git 版本一致；
    不一致时阻断布丁同步或版本发布。

## 12. 需求追踪矩阵

| Story | 核心需求 | Spec 章节 | 主要测试类型 |
|---|---|---|---|
| US-001 | Inspect | 8、10 | parser unit + temp repo integration |
| US-002 | Init | 7、8、10 | non-repo integration |
| US-003 | Workspace strategy | 11 | strategy matrix + Worktree integration |
| US-004 | Dirty protection | 10、11 | content hash + dirty repo integration |
| US-005 | Plan/approval/drift | 8–10 | hash/drift/idempotency |
| US-006 | Exact staging | 12 | literal pathspec + staged set |
| US-007 | Regression trust | 13 | config/trust/timeout/failure |
| US-008 | Commit/postflight | 12 | Commit/hook/postflight integration |
| US-009 | Record/verify | 8、9、19 | schema/privacy/drift verify |
| US-010 | Recovery | 14 | ownership/recovery integration |
| US-011 | Skill explanation | 7、18 | contract + narrative golden cases |
| US-012 | Project adapter | 13 | config compatibility |
| US-013 | Bootstrap | 20、21 | self-host + ordinary project E2E |
| US-014 | Environment doctor | 7、8、15、20 | OS/capability/PATH matrix |
| US-015 | Git/gh install | 8、15、20 | installer plan + platform sandbox |
| US-016 | Auto Git Skill install | 6、15、20 | no-Git bootstrap + host discovery + compatibility |
| US-017 | GitHub auth | 15、16、18 | credential redaction + auth states |
| US-018 | Remote create/connect | 8、16 | remote identity + GitHub adapter |
| US-019 | First Push | 8、10、16 | empty remote + upstream + postflight |
| US-020 | Subsequent Push | 8、10、16 | ahead/behind/diverged/drift |
| US-021 | Release readiness | 13、17、20 | version/changelog/build matrix |
| US-022 | Release execution | 8、12、17 | Commit/Tag/Push/Release E2E |
| US-023 | Release resume | 9、14、17 | checkpoint/idempotency/conflict |
| US-024 | Git identity setup | 8、15 | config scope/origin + Commit blocker |
| US-025 | Bilingual README/user manual/Pudding | 5、15、21 | link/parity/content golden + Pudding dry-run/postflight |

后续 TDD Plan 必须为每个 P0 Story 至少指定一个测试任务，并引用具体 Acceptance
Criteria 编号；只写“补测试”而没有 AC 映射不算需求追踪。

## 13. 异常与边界体验

| 异常 | 用户应看到 | 系统不得做 |
|---|---|---|
| 不是 Git 仓库 | 事实、init 影响、审批入口 | 自动 init |
| detached HEAD | 阻断原因、建分支建议 | 直接 Commit |
| 计划已漂移 | 变化类别、重新预览入口 | 继续旧 plan |
| 范围外 staged 文件 | 精确文件清单 | 自动 unstage 或混入 Commit |
| 回归失败 | 失败 command id、退出状态、安全下一步 | Commit 或声称通过 |
| Git hook 改文件 | 副作用事实、保留现场 | 覆盖 hook 修改 |
| lock busy | 当前操作、开始时间、诊断入口 | 静默删锁并并发写入 |
| recovery ownership 不足 | explain-only 与人工核查路径 | 删除未知 ref/Worktree/文件 |
| remote 信息可能含凭证 | 脱敏 host | 输出或保存完整敏感 URL |
| Git / GitHub CLI 缺失 | 平台、官方来源、权限和验证计划 | 自动执行猜测命令 |
| 安装需要 admin/UAC | 系统交互和权限原因 | 读取、记录或代填密码 |
| 登录账号不符 | 当前账号、目标 Owner 和切换入口 | 继续创建仓库或 Release |
| Remote 非空或身份不符 | fetch 后历史与目标身份 | 直接首次 Push |
| behind / diverged | ahead/behind 和安全同步建议 | 自动 pull/rebase/merge/force |
| Push 结果不确定 | verify 后的 applied/not-applied/unknown | 盲目重复 Push |
| Release 配置缺失 | 版本、构建、Tag、notes 的缺失清单 | 猜版本文件或构建命令 |
| 同名 Tag / Release 冲突 | OID、notes 或 assets 不一致 | 删除、覆盖或改写公开资源 |
| Release 中途失败 | 已公开 checkpoint 与 resume plan | 自动撤销远端事实 |

## 14. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| Git 版本和平台差异 | 命令在某平台失效 | capability detection + OS/Git fixture |
| Agent 误解用户审批 | 越权写入 | plan class 分离 + exact plan id/hash |
| 项目测试命令有副作用 | 修改文件或泄露信息 | 首次 fingerprint 审批、argv、timeout、postflight |
| Git hooks 修改工作区 | Core 无法自动恢复外部变化 | 检测并保留现场，不覆盖 |
| 记录泄露敏感 diff | 隐私风险 | 只保存 hash、状态、必要摘要 |
| Python 运行时漂移 | bundled scripts 行为不一致 | 声明 3.11+、capability doctor、兼容矩阵 |
| 安装命令随平台变化 | 旧命令失效或供应链风险 | 版本化平台注册表、官方来源、capability 与 postflight |
| Skill 安装器依赖 Git | 真正新手无法直接获取 Auto Git | 首次由宿主 Agent + 系统官方入口准备并验证 Git，再使用标准 Skills CLI；不另造私有安装器 |
| Python 成为 scripts 先决条件 | Skill 已安装但确定性动作不可运行 | 区分 Skill discovery 与 runtime doctor，提供官方安装引导并复评替代运行时 |
| Provider 认证泄露 | Token 进入聊天或记录 | 官方浏览器登录、系统凭证库、Token redaction |
| Push 覆盖远端工作 | 历史损坏 | fetch + ahead/behind + 禁止 force + 远端 OID postflight |
| Release 部分成功 | Tag/页面/产物不一致 | checkpoint、幂等 resume、公开资源冲突 fail closed |
| 首版范围过大 | 延迟可信闭环 | 一个纵向场景、GitHub 首适配器；PR/merge/多 Provider/包发布延后 |
| 自动化让用户失去理解 | 审批流于形式 | 每次写入解释事实、影响和恢复 |

## 15. 发布门禁

在 PRD 与 `0.1.0` Spec 未被用户确认前：

- ADR 0002 保持 Proposed；
- 不创建 TDD Plan；
- 不写实现代码或测试；
- 不 Commit、Push、创建远程仓库、tag、Release 或 Global 安装。

用户确认后，TDD Plan 必须从 `US-001` 到 `US-025` 建立 AC 追踪，并按以下纵向里程碑
拆分：环境与安装、本地核心、Remote/Push、Release、恢复与自举、用户文档与发布。
不得只按模块文件名拆任务而丢失用户结果；也不得把所有子系统塞进一个不可审查的
实施批次。
