# 2026-08-02 Auto Git 0.1.0 Spec

状态：Accepted（用户于 2026-08-03 以 Go 模式确认并授权本地开发与完整验证）

版本目标：`0.1.0`

发行修订：Accepted（用户于 2026-08-03 确认标准双远程发行、中英 README、用户手册与布丁同步）

关联：

- [Auto Git 工程宪章](../../../constitution.md)
- [Auto Git 产品定义](../../../product/product-definition.md)
- [Auto Git 0.1.0 PRD](../../../product/prd/auto-git-v0.1.0.md)
- [Auto Git 目标架构](../../architecture/auto-git.md)
- [ADR 0001：独立产品与依赖方向](../../adr/0001-independent-product-boundary.md)
- [ADR 0002：Python 核心与 JSON 契约](../../adr/0002-python-core-and-json-contract.md)
- [ADR 0003：0.1.0 零到 Release 与 GitHub 首适配器](../../adr/0003-zero-to-release-github-first.md)
- [ADR 0004：Skill-first 产品与开发治理边界](../../adr/0004-skill-first-product-and-authoring-boundary.md)
- [ADR 0005：标准 Skill 双远程发行](../../adr/0005-standard-skill-dual-remote-distribution.md)
- [标准 Skill 双远程发行 Design](../../changes/standard-distribution/design.md)
- [唯一 Handoff](../../../project/handoffs/2026-08-02-auto-git-product-foundation-handoff.md)

## 1. 背景

Auto Git 是由 Skill Engineering 创建和治理、由用户独立安装的生产级 Agent Skill。
它要让普通用户通过 Agent 的自然语言，从没有安装 Git 的电脑进入完整 Git 生命周期，
并安全走到远端 Release，同时保留标准 Git 的可读、可恢复和可迁移能力。根
`SKILL.md` 负责意图、解释、教学和审批；随 Skill 分发的 `scripts/` 负责读取机器
事实、生成不可漂移计划、执行、验证、记录和恢复。

`0.1.0` 建立从 Auto Git/Git 安装、本地 Commit、标准 Remote、Push 到 GitHub Release
的最小可信纵向闭环。PR、merge、force push 和包注册表发布不进入本版本。

## 2. Discovery 结论

### 2.1 ANK `.new` 审查

ANK profile 生成了 11 个 `.new`。它们不能整体覆盖现有文件。

| 产物 | 判定 | 处理 |
|---|---|---|
| `CLAUDE.md.new` | adopt | 后续手工补入一行产品描述 |
| `docs/knowledge/references/legacy-layout/README.md.new` | reject overwrite | 保留现有 Auto Git 文档地图，不用通用英文模板替换 |
| `docs/knowledge/references/legacy-layout/constitution.md.new` | reject | 现有宪章是产品事实源；新文件含日期占位符且会丢失 12 条产品原则 |
| `factory-check.md.new` | adapt | skillhub disabled 时应明确跳过；自然语言技术选型说明不能作为 shell 命令 |
| `task-sync.md.new` | adopt after review | profile 字段已正确回填，但外部写入仍遵守 dry-run/apply 门禁 |
| `harness-sop.md.new` | adapt | skillhub disabled 时不运行 diff；不能仅因路径已回填就启用依赖 |
| `rules-six-redlines.md.new` | adopt after review | 项目红线、危险命令和文档范围已正确回填 |
| `sop-feature.md.new` | adapt | 路径字段可采纳；`build_command` 要等本 Spec 确认后改成真实命令 |
| `task-sync-sop.md.new` | adopt after review | 非敏感 task 指针可回填 |
| `settings.json.new` | reject current form | 含无效自然语言 Bash allow 项，且仍有 `lint/test` 占位符 |
| `_ob-task-sync-template.md.new` | adapt | 配置值可采纳；模板实例日期仍应由创建动作填写 |

活跃运行入口仍有未解释占位符，集中在 `.claude/rules/*`、两个 command 和
`.claude/settings.json`。`AGENTS.md` 的通用占位符说明及 hook 中的 brace 示例不是
生成占位符。入口清理属于实现前置任务，必须按逐文件 diff 合并，禁止覆盖
Product、Constitution 或用户定制内容。

### 2.2 本机资产 adopt / adapt / defer / reject

| 资产 | 判定 | 原因 |
|---|---|---|
| `agent-skill-hub` 的 plan hash、source/target fingerprint、record、verify、safe undo | adapt | 机制已验证，但它面向 Skill 链接安装；Auto Git 必须建立 Git 专用事实与恢复契约 |
| ANK `ank-install-githooks` | adapt | 采用 dry-run、marker ownership、冲突写 `.new`；Auto Git 不依赖 ANK |
| ANK Git `pre-commit` dispatcher | adopt pattern | hook 保持薄壳、检查逻辑在独立脚本；hook 缺失不等于核心检查通过 |
| ANK `ank-worktree` / `ank-task` | adapt | 采用 `git -C` 与“不自动搬运脏改动”；状态读取需升级为 porcelain v2/NUL |
| `using-git-worktrees` Skill | adapt | 采用现有隔离检测、submodule guard、基线测试；Worktree 由风险策略决定 |
| GitHub `yeet` Skill | adapt | 采用 scope/diff/精确 staging 与 Push 前确认；拒绝 `git add -A` 和“一次批准完成 Commit+Push” |
| 三仓 `credential-lint.sh` | adapt | 可作为项目回归命令；模式和凭证规则不能成为核心硬编码 |
| Skill Engineering Python CI | adapt | 采用 Python 多版本、pytest、ruff、credential lint、`git diff --check` 思路 |
| GitHub CLI auth/repo/release | adapt | 作为首个 Provider Adapter；登录交给浏览器/凭证库，创建仓库不顺带 Push，Release 必须验证既有 Tag |
| GitLab/Gitee Provider Skill | defer | 标准 Remote 可连接和 Push；专用仓库创建与 Release API 延后 |
| 纯 Agent 规则直接运行写入型 Git | reject | 无不可变计划、漂移检测、锁和 postflight |
| 纯 shell 核心 | reject | 难以稳定处理 NUL 输出、schema、跨平台锁、幂等和恢复 |

### 2.3 产品运行形态比较

| 方案 | 用户安装对象 | 确定性边界 | 运行成本 | 结论 |
|---|---|---|---|---|
| Skill-first + bundled scripts | 只安装 Auto Git Skill | Git 逻辑在 Skill 的 `scripts/`，根 Skill 只编排 | 最低；仍可独立测试和版本化 | 推荐 |
| Skill + 独立 pipx CLI | 同时安装 Skill 与 CLI | JSON CLI 边界清楚 | 双重安装、PATH 和版本配对增加新手负担 | `0.1.0` 拒绝 |
| MCP Server | 安装 Skill/客户端并配置服务 | MCP tool schema | 需服务进程、认证与生命周期管理 | 无明确服务化需求，延后 |

Auto Git `0.1.0` 采用 Skill-first。Skill Engineering 是开发期治理入口，不是运行时
delegate。用户不会被要求额外安装 Skill Engineering、独立 Auto Git CLI 或 MCP。

### 2.4 Scripts 实现语言比较

| 方案 | 安装与跨平台 | Git 进程安全 | schema/测试 | 当前成本 | 结论 |
|---|---|---|---|---|---|
| Python 3.11+，标准库优先 | 随 Skill 放在 `scripts/`；宿主运行前 doctor Python capability | `subprocess` 参数数组，默认不经 shell | dataclass/JSON、pytest 成熟 | 最低；本机已有相邻范式 | 推荐 |
| Node.js | npm 入口方便；单文件分发仍在演进 | `spawn/execFile` 参数数组可安全使用 | JSON 原生，测试成熟 | 本机多 Node 来源且项目未钉版本 | 备选 |
| Rust | 单二进制、跨平台分发最好 | `Command` 参数分离和类型约束强 | serde/测试强 | 本机无工具链，首版成本最高 | 后续复评 |

决定采用 Python 3.11+ 编写 Skill 内 `scripts/`，核心运行时只依赖标准库。开发依赖
允许 pytest、ruff 和构建后端。实现不得依赖当前 PATH 中的 notebooklm Python；开发
项目必须声明版本并通过项目虚拟环境运行，用户环境必须由 doctor 验证真实 capability。

## 3. 目标

1. 对 Git 仓库和非 Git 目录生成机器可读事实。
2. 对 init、workspace、commit 和 recover 生成不可变计划。
3. Apply 只接受用户已看到的同一 plan id + plan hash；漂移后必须重新预览。
4. 精确 stage 用户批准的文件，永久禁止 `git add -A` 和 `git add .`。
5. 运行可信的项目回归档位，失败、超时或命令缺失时阻断 Commit。
6. Commit 前保护 index，Commit 后验证 HEAD、提交范围和记录。
7. 失败时不丢工作区文件；只撤销本次操作拥有且未漂移的资产。
8. 交付可被宿主发现的 Auto Git Skill、自然语言入口、解释和基础训练模式。
9. 使用 Auto Git 自身完成一次自举，并在一个普通项目验证可信接入。
10. 验证 Auto Git Skill 的安装/发现/升级/卸载，并在受支持平台检测和指导安装 Git、
    Python 与 GitHub CLI。
11. 创建或连接正确 Remote；基于 fetch 后事实生成首次和后续 Push 计划。
12. 用 release profile 固定版本、变更日志、回归、构建、Tag、notes 和 assets。
13. Release Commit、annotated Tag、branch Push、Tag Push、GitHub Release 分别审批。
14. 发布中断后根据本地与远端事实 checkpoint 幂等继续，不删除或改写公开历史。

## 4. 非目标

- PR、merge、force push 和自动冲突解决；
- GitLab/Gitee 专用账号、仓库创建与 Release Provider；
- Auto Git 自身的 Gitee 镜像仓库不属于 Gitee Provider Adapter；它只使用标准 Git
  Remote/Push/Tag Push；
- PyPI、npm、容器 Registry、应用商店等包发布；
- 后台监控目录或常驻 daemon；
- 自动 stash、自动搬运脏改动或自动解决冲突；
- 云服务、模型 Provider、凭证托管；
- ANK 运行时集成、Skill Engineering 运行时 delegate；
- 独立 pipx CLI、MCP Server、root/admin 系统级安装和单文件二进制发布；
- 完整训练营课程平台。

## 5. 用户故事

完整 User Stories、角色、主流程和 Given/When/Then 验收条件见
[Auto Git 0.1.0 PRD 第 11 节](../../../product/prd/auto-git-v0.1.0.md#11-user-stories-与验收条件)。

本 Spec 对应的需求范围：

| Story | 技术责任 |
|---|---|
| US-001、US-002、US-003、US-004 | inspect、init、workspace strategy、dirty protection |
| US-005、US-006、US-007、US-008 | immutable plan、exact staging、regression、Commit/postflight |
| US-009、US-010 | operation record、verify、ownership-aware recovery |
| US-011、US-012 | Skill explanation、project regression adapter |
| US-013 | Auto Git 自举与普通项目 E2E |
| US-014、US-015、US-016 | environment doctor、Git/gh installer、Skill install/discovery lifecycle |
| US-017、US-018 | GitHub auth、Remote create/connect |
| US-019、US-020 | first/subsequent Push、ahead/behind、remote postflight |
| US-021、US-022、US-023 | release readiness、phased Release、checkpoint/resume |
| US-024 | Git identity/config scope 与 Commit blocker |
| US-025 | bilingual README、user manual、Pudding publication projection |

后续 TDD Plan 与测试必须引用具体 Story/Acceptance Criteria 编号，不能只引用本 Spec 的
技术模块。

### 5.1 Skill 触发与反触发

正触发至少包括：

- “帮我检查这个项目有没有用 Git。”
- “我电脑没有 Git，帮我安装并初始化这个项目。”
- “这次修改能不能提交？先给我看计划。”
- “帮我创建或连接远程仓库，先不要 Push。”
- “把当前版本 Push 上去。”
- “检查并发布 `0.1.0`。”
- “恢复 Auto Git 上一次操作，但不要丢文件。”

反触发至少包括：

- 只要求解释一段代码、写文章或处理与版本管理无关的文件；
- 只询问 Git 概念且不要求检查或修改真实仓库；
- 要求直接 PR、merge、force push、解决冲突或发布到包注册表；
- 要求保存 Token、私钥、Cookie 或绕过项目测试/远端保护；
- 要求管理 Auto Git Skill 自身版本、安装范围或候选发布时，应交给 Skill
  Engineering/宿主 Skill 安装治理，而不是让 Auto Git 自修改。

## 6. 总体架构

```text
自然语言用户
  ↓
Auto Git SKILL.md
意图枚举 / 路径确认 / 风险解释 / 教学层级 / 审批断点
  ↓ versioned JSON script contract
Auto Git bundled scripts
doctor → inspect → strategy → immutable plan → apply → verify → record → recover/resume
  ↓ argv，无 shell
标准 Git / OS package manager / GitHub CLI
```

Skill Engineering 只在开发期生成、审查、评测和维护上述 Skill 包，不出现在运行数据
流中。目标 Skill 结构为：

```text
SKILL.md
skill.contract.yaml
agents/openai.yaml
scripts/
references/
tests/skills/auto-git/cases/
docs/
```

可选目录没有真实内容时不创建。根 `SKILL.md` 保持轻薄，复杂状态机和机器判断不得
以内联命令或自然语言规则代替。

### 6.1 Scripts 模块

| 模块 | 单一职责 |
|---|---|
| `git_runner` | 用 argv 调用 Git，固定 cwd、timeout、环境边界和错误模型 |
| `environment` | 检测 OS、架构、PATH、Python、Git、GitHub CLI 与 capability |
| `installer` | 从版本化平台注册表生成安装计划，执行后重新探测，不处理密码 |
| `inspect` | 读取 porcelain v2/NUL、refs、HEAD、index、worktree、remote 与能力 |
| `models` | schema version、JSON canonicalization、plan/record 数据模型 |
| `state` | 本机状态目录、原子写、锁、idempotency 和记录读取 |
| `strategy` | 当前分支/功能分支/Worktree 决策，不执行 Git |
| `planner` | 生成 install/init/workspace/commit/remote/push/release/recover 计划和 preconditions |
| `regression` | 配置读取、信任校验、argv 执行、timeout 和结果摘要 |
| `executor` | 审批断言、漂移复验、精确执行和失败补偿 |
| `remote` | fetch、remote identity、upstream、ahead/behind、Push 与远端 ref postflight |
| `release` | release profile、readiness、版本/Tag/notes/assets 与 checkpoint 状态机 |
| `github_adapter` | 调用官方 `gh` 做 auth status、repo create 和 release create/verify |
| `recovery` | index 恢复、恢复 ref、soft uncommit 等无文件丢失方案 |
| `redaction` | 路径、命令输出和错误信息的最小保存/脱敏 |
| `script_entry` | 人类文本与 `--json` 两种稳定输出；不承载业务规则 |

### 6.2 `skill.contract.yaml`

作为生产级副作用 Skill，contract 至少声明：

- `inputs`：目标项目、intent、task kind、risk、selected paths、feedback level；
- `outputs`：facts、plan、approval request、record、verification、recovery availability；
- `stops`：环境不支持、事实不足、计划漂移、审批缺失、回归失败、远端分叉、恢复不安全；
- `delegates`：只允许调用 Skill 内已登记 scripts、标准 Git、受信项目回归和 GitHub
  CLI Adapter；
- `forbidden`：凭证接收、自由 shell、宽泛 staging、force push、未知资产删除、隐式
  Push/Tag/Release；
- `state`：本机 repo-scoped plan/record/checkpoint/trust，不把运行状态写入项目；
- `approvals`：install dependency、git config、init、workspace、Commit、remote、
  Push、Tag、Release、recover 分别声明；
- `scripts`：入口、参数、JSON schema、timeout、dry-run/plan 与 apply 的关系；
- `tests` 与 `evaluation`：success、failure、high-risk、baseline、holdout、真实任务
  rollout 和独立评审要求。

contract 是 `SKILL.md`、scripts 和测试的共同事实源；候选生成时不得只创建空骨架。

## 7. Skill 与 Scripts 边界

### 7.1 0.1.0 脚本调用面

```text
<python> <skill-root>/scripts/auto_git.py doctor --repo <path> [--json]
<python> <skill-root>/scripts/auto_git.py dependency-plan --dependency <git|gh>
  [--system <darwin|linux|windows>] [--json]
<python> <skill-root>/scripts/auto_git.py auth-status --provider github [--json]
<python> <skill-root>/scripts/auto_git.py inspect --repo <path> [--json]
<python> <skill-root>/scripts/auto_git.py plan --repo <path> --action <action>
  [--params-json <json-object>] [--output <plan.json>] [--json]
<python> <skill-root>/scripts/auto_git.py apply --plan <plan.json> --approval <plan-hash>
  [--state-home <path>] [--json]
<python> <skill-root>/scripts/auto_git.py verify --record <record.json> [--json]
<python> <skill-root>/scripts/auto_git.py plan-recover --repo <path> --record <record.json>
  --state-home <path> [--output <plan.json>] [--json]
<python> <skill-root>/scripts/auto_git.py recover --plan <plan.json> --approval <plan-hash>
  --state-home <path> [--json]
<python> <skill-root>/scripts/auto_git.py release-check --repo <path> --version <version>
  [--profile <path> | --profile-json <object>] [--regression-json <argv-arrays>]
  [--build-json <argv-arrays>] [--json]
<python> <skill-root>/scripts/auto_git.py resume --repo <path> --version <version>
  [--remote <name>] [--json]
<python> <skill-root>/scripts/auto_git.py verify-mirrors --repo <path>
  --remote <name> --remote <name> --branch <branch> [--tag <tag>] [--json]
<python> <skill-root>/scripts/auto_git.py history --repo <path>
  [--state-home <path>] [--json]
```

`<python>` 是宿主只读探测后确认满足 3.11+ 的真实可执行文件；不能假设所有平台都叫
`python3`。`<skill-root>` 由宿主的 Skill 发现结果提供，不写死用户目录。

公开 `plan` 的 `<action>` 精确限定为：

```text
init
configure_identity
stage_commit
remote_connect
github_repo_create
push
tag
push_tag
github_release
```

自然语言中的 install、workspace、commit、remote-create、remote-connect 和 release
阶段由根 Skill 映射为上述确定性 action 与 `params-json`；脚本不自行理解自然语言。
`recover_index` 是内部 action，公开入口只能通过 `plan-recover` 从受管 operation record
生成，禁止用普通 `plan` 手写恢复参数。

`release-check` 默认读取目标仓库 `.auto-git.toml` 的 `[release]`。`--profile-json`
只用于已经由宿主从可信项目配置解析出的等价机器对象和隔离测试；缺 profile 时返回
`ready=false`，不猜测发布分支、Remote、测试、构建或 assets。

Auto Git Skill 自身的安装、升级和卸载由宿主 Skill 安装器或已校验发布归档负责，
不由 bundled script 自修改。安装后必须分别验证宿主发现、Skill 版本/contract 与
Python scripts capability。

`--approval` 必须精确等于刚展示且未漂移计划的 `plan_hash`。它不是“证明用户说过
同意”的替代品；Agent Skill 必须先取得用户对该动作的明确审批，核心再强制
preview/apply 分离、计划哈希、仓库 fingerprint 与动作级边界。

每个 plan 只属于一个审批类：

```text
configure-identity
init
workspace
commit
remote-connect
remote-create
push-branch
tag-create
push-tag
github-release
recover
```

其中 install-dependency 是只读指导计划，不进入通用 `apply`；workspace 是根 Skill
根据 facts 给出的策略建议，不是 0.1.0 Core 写入 action。Commit plan 可以把精确
staging、required regression 和 Commit 组成一个可补偿批次，
但不能顺带创建 Remote 或 Push。GitHub remote-create 不得使用 `gh repo create --push`。
Release 是一个带 checkpoint 的父工作流，但 Release Commit、Tag、branch Push、Tag Push
和 GitHub Release 分别生成子计划并分别批准。

### 7.2 根 Skill 可以做

- 把自然语言映射为固定 intent、task kind、risk、paths 和 feedback level；
- 调用只读 inspect/plan；
- 用普通语言解释 branch、Worktree、stage、Commit 和恢复；
- 展示 plan id、hash、文件清单、安装来源、Remote/Owner、回归档位和审批影响；
- 用户批准后调用 apply，并展示 postflight。

### 7.3 根 Skill 不可以做

- 自己解析 porcelain 文本并推断状态；
- 绕过 bundled scripts 直接运行写入型 Git；
- 生成或修改 plan JSON 后继续 apply；
- 把聊天中的模糊“可以”跨动作复用为 Commit、Push 或恢复审批；
- 请求用户在聊天中粘贴密码、Token、Cookie 或私钥；
- 把 GitHub 仓库创建与 Push 合并，或让 GitHub Release 隐式创建 Tag；
- 在训练模式中降低安全门禁。

### 7.4 Scripts 不可以做

- 理解或补写模糊自然语言意图；
- 把没有动作级 approval assertion 的调用当作用户已经同意；
- 直接调用 Skill Engineering、Agent 模型或 MCP Server；
- 安装、升级或卸载 Auto Git Skill 自身；
- 根据聊天内容猜测仓库、账号、Remote、版本或发布状态。

## 8. 仓库事实与 schema

所有 JSON 顶层包含：

```json
{
  "schema_version": "1",
  "kind": "inspect_report",
  "id": "inspect-...",
  "created_at": "UTC ISO-8601",
  "repo_id": "sha256:...",
  "status": "ok"
}
```

### 8.1 `InspectReportV1`

至少包含：

- canonical repo/worktree root（终端输出可显示；持久记录默认只保留 `repo_id`）；
- `is_git_repo`、`is_bare`、`is_linked_worktree`、`is_submodule`；
- HEAD：unborn / branch / detached、OID、upstream；
- git common dir 与当前 worktree identity；
- index 状态、冲突、staged/unstaged/untracked/ignored 摘要；
- remotes 只记录名称和脱敏 host，不保存带凭证 URL；
- Git 版本与 capability；
- `repo_fingerprint` 和结构化 warnings/blockers。

Git 状态读取使用 `git status --porcelain=v2 -z --branch --untracked-files=all`。解析器必须
按 bytes/NUL 处理 rename、空格、Unicode、换行和 `-` 开头路径，禁止按可视行拆分。

`repo_id` 是当前机器上 canonical git common dir 的 SHA-256；非 Git 目录使用预期
`<root>/.git` 作为 identity，因此 init 前后保持一致。`worktree_id` 另由 canonical
worktree root 与 git dir 计算。仓库移动后得到新 id，旧记录保留但不自动迁移。

### 8.2 `OperationPlanV1`

至少包含：

- `id`、`operation`、`repo_id`、`schema_version`；
- 用户可见 summary、risk、approval requirement；
- exact actions：program、argv、cwd policy，不保存 shell 字符串；
- selected literal paths、回归 profile、Commit message 正文与 hash；
- preconditions：HEAD、branch、index digest、status digest、selected path fingerprints；
- expected postconditions、rollback summary、expiry policy；
- canonical `plan_hash`。

Plan 以 canonical JSON（UTF-8、key 排序、稳定 separators）计算 SHA-256。`plan_hash`、
approval 和 execution 字段不进入自身哈希。Plan 创建后原子写入且不可覆盖。
`0.1.0` 不设置基于时间的过期；任何 precondition/fingerprint 漂移都会立即使 plan
失效。Commit message 由 plan 本地保存，record 默认只保存 message hash 和 subject，
apply 不重新读取可能已经变化的外部 message file。

### 8.3 `OperationRecordV1`

至少包含：

- plan id/hash、approval assertion、started/finished；
- pre/post fingerprint；
- 执行动作的程序与 argv、退出码、耗时；
- 回归 command id、退出码、耗时和输出摘要 hash；
- created refs/worktrees/index backup 等 ownership；
- Commit OID、verification checks、status、warnings；
- 可用 recovery modes。

默认不持久化完整 diff、文件内容、完整 stdout/stderr、token、Cookie、私钥或带凭证
remote URL。

### 8.4 `EnvironmentReportV1`

至少包含：

- OS family、发行版、版本、架构和 shell；
- Python、Git、GitHub CLI 的 executable path、版本与状态；
- Git identity 的 effective name、脱敏 email、origin 和 local/global/system scope；
- PATH 冲突、支持级别、Git capability 和是否需要 shell restart；
- GitHub auth 只包含 hostname、account、protocol、validity，不包含凭证；
- 组件状态枚举：`ready`、`missing`、`outdated`、`conflict`、`auth_required`、
  `unsupported`。

### 8.5 `SkillInstallReportV1`

由宿主 Skill 安装器或发布归档验证器产生，至少包含：

- Auto Git Skill source、version、target host、scope 和 target identity；
- manifest 中 `SKILL.md`、contract、scripts、references、tests 的存在与 hash；
- 安装记录拥有的文件范围和可撤销方式；
- 宿主 discovery、正触发、反触发与版本读取结果；
- bundled scripts 的 Python capability 状态；
- `installed`、`discovered`、`runtime_ready` 分层状态，禁止用文件存在冒充完整可用。

### 8.6 `InstallerPlanV1`

在通用 plan 字段外至少包含：

- component、platform selector、source class、official source URL；
- package manager/installer program + argv、是否需要 admin/UAC/GUI；
- registry revision、expected executable、version/capability policy；
- postflight probe 与 `restart_shell_required` 判定。

安装注册表是可测试的数据文件，不允许由 Agent 临时拼接命令。未匹配的平台不产生
apply action。安装执行不得接收密码或 Token，也不得静默切换镜像。

### 8.7 `RemoteFactsV1`

至少包含：

- remote name、sanitized host、Provider、Owner/repo identity；
- fetch result、default branch、目标 branch/ref OID；
- upstream、ahead、behind、diverged 和 remote-empty 状态；
- GitHub auth account、visibility、permission summary（适用时）；
- `remote_fingerprint`，覆盖 URL identity、fetch 后 ref OID 和认证账号。

### 8.8 `ReleasePlanV1` 与 `ReleaseCheckpointV1`

父 Release plan 至少固定：

- source/target version、version files、changelog section；
- allowed branch、Release Commit subject、required full regression；
- build argv、asset path + SHA-256、notes source + hash；
- annotated Tag 名称、target Commit OID、Remote/Provider；
- 有序子步骤和各自 approval class。

每个 checkpoint 记录 `planned|applied|verified|failed|unknown`、本地/远端 OID、Provider
resource id/URL 和 verification checks。Resume 必须先重读本地与远端事实；只有资源
身份和内容与 plan 一致时才能跳过已完成步骤。同名资源不一致时 fail closed。

## 9. 本机状态、锁与幂等

- 状态放在平台用户 state 目录的 `auto-git/repositories/<repo_id>/`，不进入项目仓库。
- 可用 `AUTO_GIT_STATE_HOME` 指定测试/便携状态根；真实凭证不能放入该变量值。
- plans、records、verifications、backups 分目录，JSON 通过临时文件 + atomic replace 写入。
- Apply/Recover 使用 per-repo 原子锁；锁包含 PID、操作和开始时间。
- 活锁直接返回 `lock_busy`；疑似 stale lock 只报告，需 doctor/明确恢复，不能静默删除。
- 同一 plan 重复 apply：若已有 verified record 且 postcondition 仍成立，返回原记录；
  若状态不一致，返回 drift/partial，不重复执行。

## 10. Fingerprint 与漂移

`repo_fingerprint` 组合以下摘要：

1. repo/worktree identity；
2. HEAD OID 与 branch/unborn/detached 状态；
3. `git ls-files --stage -z` 的 SHA-256；
4. porcelain v2/NUL 原始 bytes 的 SHA-256；
5. selected paths 的类型、mode、size、symlink target/content SHA-256；
6. 影响策略的项目配置 fingerprint。

Commit apply 默认要求完整 status digest 未变化。即使变化发生在未选文件，也重新
plan；`0.1.0` 选择 fail closed，避免混入 Agent 不曾展示的新事实。

非 Git 目录使用 `directory_fingerprint`：canonical root、`.git` 不存在、相对路径、
文件类型、mode、size 与 mtime 的稳定摘要。init plan apply 前目录事实变化也重新
plan；不为只读预览持久化文件内容。

## 11. 工作区策略

| 事实 | 默认策略 |
|---|---|
| 非 Git 目录 | 只生成 init plan；批准后 `git init` |
| 已在 linked worktree | 不嵌套创建 Worktree |
| detached HEAD | 阻断 Commit，先生成建分支计划 |
| 功能分支、改动单一且无并行任务 | 当前 checkout |
| `main/master` 干净，普通功能 | 当前 checkout 新建功能分支 |
| `main/master` 脏，但全部改动属于当前任务 | 当前 checkout 新建分支，保留脏文件 |
| 脏改动与新任务无关 | 从 HEAD 创建新 Worktree；原改动留在原 checkout |
| 并行任务、重构或高风险 | 优先 Worktree |
| 基线回归失败 | 不开始写入；报告并请求用户决定后续诊断 |

`0.1.0` 的 workspace 策略不自动 stash、不自动把脏改动搬到 Worktree，也不在正常
收尾时删除 branch/Worktree。只有 recover 可以对本 operation 创建且仍干净的
Worktree 生成单独审批的删除计划。

## 12. 精确 staging 与 Commit

### 12.1 Plan

- 用户/Skill 必须显式传入每个 repo-relative path；
- path 规范化后必须仍位于 repo root，拒绝空路径、repo root、`.git` 和路径逃逸；
- 展示 selected、excluded、已 staged、删除/rename/submodule 等特殊项；
- 已 staged 的范围外文件直接阻断；
- 永不生成 `git add -A` 或 `git add .`。

### 12.2 Apply

1. 获取 per-repo lock；
2. 复验 plan hash、approval assertion 和全部 preconditions；
3. 备份当前 index 到本机 operation backup；
4. 使用 `git --literal-pathspecs add --pathspec-from-file=- --pathspec-file-nul`，
   通过 stdin 发送 NUL 分隔的精确路径；
5. 验证 staged path set 与计划完全一致；
6. 运行 required regression；
7. 使用 message 临时文件执行 `git commit --file <path>`，不通过 shell；
8. postflight 验证 HEAD 变化、Commit OID、提交路径、状态和 hook 结果；
9. 保存 record 和 verification。

任何 Commit 成功前的失败都恢复 apply 前 index；Core 自身不改工作区文件。Git hook
若修改工作区，postflight 必须报告 `external_side_effect_detected`，保留文件并停止，
不得用旧 fingerprint 覆盖。Commit 成功后若 postflight 异常，不自动回退 Commit；
记录 `verification_failed` 并提供恢复计划。

## 13. 回归档位与命令信任

### 13.1 档位

- `integrity`：内置 Git 检查、冲突检查、staged `git diff --check`；
- `quick`：项目配置的快速 lint/unit；
- `full`：功能、重构和高风险任务的完整项目回归；
- `docs`：项目显式配置的文档检查；未配置时仍运行 `integrity`。

功能任务必须有 `full`；补丁至少 `quick`；纯文档至少 `docs` 或明确配置为
`integrity`。required profile 缺失、命令失败、timeout、signal 或 executable 缺失都
阻断 Commit，不能用聊天文本伪造“已通过”。

### 13.2 信任

- 项目配置使用 repo 内 `.auto-git.toml`，只允许 argv 数组，不接受任意 shell 字符串；
- 首次出现的配置 fingerprint 必须经用户批准并写入本机 trust record；
- 配置变化后信任失效，重新预览；
- 工作区中未提交的配置不能自动运行，但可在展示完整 argv 与 fingerprint 后由用户
  显式建立本机信任；
- 核心移除会改变 Git 目标的 `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE` 等环境变量，
  仅按明确内部操作设置；
- 命令输出可实时展示，默认不完整持久化。

## 14. 恢复

`0.1.0` 提供以下可证明安全的恢复模式：

1. `restore-index`：Commit 前失败时恢复 operation 拥有的 index backup；
2. `remove-created-worktree`：仅当 Worktree 由本 operation 创建、仍无新增改动且 ref
   未漂移时才允许计划删除；实际删除仍单独审批；
3. `soft-uncommit`：只针对 Auto Git 记录的最新本地 Commit；先创建
   `refs/auto-git/backups/<record-id>`，再计划 `git reset --soft <parent>`，保留
   文件和 index；HEAD 漂移、Commit 可从本地 remote-tracking ref 到达或远程事实
   不足时拒绝；
4. `checkpoint-ref`：在进一步恢复前先保留当前 OID；
5. `explain-only`：任何无法证明 ownership 或无损性的场景只给诊断与人工路径。

禁止自动使用 `reset --hard`、`clean -fdx`、force push、删除未知 branch/Worktree，
也不把 stash 当作默认备份。

## 15. 环境与安装

### 15.1 Auto Git Skill 分发

- 用户安装对象是 Auto Git Skill，不是独立 Python 包或 CLI；
- 安装、升级和卸载遵循标准 Skills CLI 或宿主原生 Skill 管理器，不创建
  `install.sh`、`install.ps1` 或 Auto Git 私有安装协议；
- GitHub 是主发行仓库和标准简写安装源；Gitee 是同一 Commit、同一版本的标准 Git URL
  镜像安装源；
- 安装计划必须固定 source、version、target host、project/global scope、标准安装器
  行为和可撤销 ownership；
- GitHub/Gitee 两源安装后必须验证 Skill version、manifest 和关键文件 hash 一致；
- 已验证当前标准仓库型 Skills CLI 对普通 GitHub owner/repo 和 Gitee Git URL 使用
  clone，因此 Git 是 Auto Git 首装前置条件；
- 无 Git 且尚未安装 Auto Git 时，由当前宿主 Agent 通过系统官方/受信任包管理器
  指导安装 Git，用户批准后以 `git --version` 和 PATH 复验，再安装 Auto Git；
- 不得声称尚未安装的 Auto Git 能先运行 doctor，也不得以自建安装器或私有 Release
  ZIP 掩盖前置条件；
- postflight 分三层报告：文件/manifest 完整、宿主发现/触发通过、Python scripts
  capability 通过；前两层通过但 Python 缺失时只能报告“Skill 已安装，确定性动作尚
  不可用”；
- Python 3.11+ 缺失时，bootstrap 阶段只提供受支持平台的官方安装引导和验证步骤，
  不用尚不能运行的 Python script 假装执行 Python 安装；
- 升级必须展示 from/to、文件 diff、contract/schema 兼容和恢复路径；卸载只移除安装
  记录拥有的 Skill 文件，项目仓库、Git 历史和 operation records 默认保留；
- 独立 pipx CLI、单文件二进制、MCP 和自建 Shell/PowerShell 安装器待真实需求出现后
  单独 ADR。

标准命令形态：

```text
npx skills add <github-owner>/auto-git
npx skills add https://gitee.com/<gitee-owner>/auto-git.git
npx skills add <source> -g -a codex -a claude-code
npx skills update auto-git
npx skills remove auto-git
```

最终 README 必须解释 source、`-g`、`-a`、project/global 影响和各命令前置条件。

### 15.1.1 Auto Git 自身双远程发行

- 本地 remote 计划命名为 `origin`（GitHub）和 `gitee`（Gitee）；
- 真实 Owner、URL、visibility 和默认分支从机器事实及用户选择取得，不在文档中猜测；
- GitHub 与 Gitee 仓库创建/连接分别审批；两次 Push 分别预览和审批；
- 只有 `local HEAD = GitHub branch OID = Gitee branch OID` 时才能报告源码同步完成；
- 同步版本 Tag 时，必须验证两个远端 Tag 的 target Commit 与本地 annotated Tag 一致；
- Gitee 专用登录、API 建库和 Release API 不进入 0.1.0；没有受控 Adapter 时由用户在
  官方界面建库，Auto Git 只连接已确认 URL；
- 任一远程失败时保留已成功事实并生成 resume，不 force push、不删除公开资源。

### 15.1.2 用户文档与布丁发布

- `README.md` 为中文主入口，`README.en.md` 为英文入口；两者顶部互相链接；
- 两版 README 必须对齐产品定位、版本、功能、标准安装、GitHub/Gitee 来源、安全边界、
  支持宿主、用户手册和反馈入口；
- 中文用户手册事实源为
  `docs/knowledge/users/guides/auto-git-user-manual.zh-CN.md`，只面向普通用户，不混入 PRD、ADR、
  TDD、Skill Engineering 治理或开发者自测说明；
- 用户手册按“可复制的自然语言 → Auto Git 行为 → 审批点 → 预期结果 → 故障处理”
  组织，覆盖安装到 Release、恢复、更新和卸载的基本闭环；
- 布丁发布副本位于
  `/Users/aim5/Documents/OB/_OB工程/publications/auto-git/Auto Git 用户手册.md`；
- 仓库手册是公开产品事实源，OB 副本是布丁 projection；去除平台 frontmatter 后正文
  与版本必须一致；
- 布丁 dry-run 使用 `pudding sync <file>`，确认预览后才使用同一目标加 `--apply`；
  postflight 使用 `pudding status <file>` 并记录工具真实回填的 case id、后台 URL 与
  draft/published 状态；只有 published 才要求公开 URL；
- `pudding_id`、后台 URL、同步时间等布丁环境元数据只留在 OB 副本，不进入公开仓库；
- 布丁同步失败不影响本地 Skill 功能，但阻断“用户手册已发布”的完成声明。

### 15.2 Git 与 GitHub CLI

版本化 installer registry 首批支持：

| 平台 | Git 策略 | GitHub CLI 策略 |
|---|---|---|
| macOS | Xcode Command Line Tools 或 Git 官方安装入口；已有 Homebrew 时可选 brew | GitHub 官方 Homebrew/binary |
| Windows | Git for Windows 官方入口；已有 WinGet 时可选其精确 package id | GitHub 官方 WinGet/MSI |
| Debian/Ubuntu | 发行版 apt 包 | GitHub 官方 apt repository |
| Fedora/RHEL | 发行版 dnf 包 | GitHub 官方 rpm repository |
| 其他 | explain-only + Git 官方入口 | explain-only + GitHub CLI 官方入口 |

registry 必须区分官方项目包、操作系统包和社区包，不把社区来源冒充官方。安装前固定
registry revision 和命令；安装后从新进程重新探测 PATH、版本和 capability。

### 15.3 权限与凭证

- admin/sudo/UAC/GUI 交互必须在 plan 中显示；密码始终由系统处理；
- GitHub 默认使用 `gh auth login` 浏览器流程；
- Core 只消费 `gh auth status` 的脱敏事实；
- 若 `gh` 警告无法使用系统凭证库并将降级到明文文件，必须在继续前单独告警；
- 禁止 `--with-token`、argv Token、聊天粘贴 Token 或把 `GH_TOKEN` 写入计划/记录。
- 用户没有 GitHub 账号时，只指向官方注册与邮箱验证流程并建议 2FA；Auto Git 不代填
  资料或创建账号，用户也可以改用其他标准 Git Remote。

### 15.4 Git 首次配置

- doctor 使用 `git config --show-origin --show-scope` 读取有效 `user.name`、
  `user.email` 和 `init.defaultBranch`；
- identity 缺失时阻断 Commit plan；
- config plan 必须让用户选择当前仓库 `local` 或当前系统用户 `global`，不写 system；
- 姓名和邮箱可建议但不得从 GitHub/OS 静默推断后写入；
- 邮箱只在当次 plan 中用于执行，长期 record 默认只保存 hash、scope 和 origin；
- `init.defaultBranch` 只影响未来 init，不重命名已有仓库分支；
- 写入后重新读取 effective value、origin 和 scope 才能 verified。

## 16. Remote 与 Push

### 16.1 Remote create/connect

- 标准 Remote identity 是 protocol + sanitized host + owner/path；user-info、query 和
  credential 必须拒绝或脱敏；
- connect 只添加/修改一个明确 remote name，名称冲突时 fail closed；
- GitHub create 固定 authenticated account、Owner、repo、visibility；
- visibility 是必填项，不从账号默认或聊天语气推断；
- `gh repo create` 不带 `--push`；创建仓库与 Push 属于不同 operation；
- 创建/连接后必须 fetch 或读取 Provider 事实，确认 Remote 是否为空。

### 16.2 Push plan

生成计划前必须 fetch，并固定：

- remote identity、local branch/OID、target ref/current remote OID；
- upstream、ahead、behind、diverged；
- 将公开的 Commit OID 列表/subject 摘要；
- required regression record/fingerprint；
- expected remote OID 与是否设置 upstream。

behind、diverged、remote identity/auth 变化、回归过期、secret protection 或
non-fast-forward 都 fail closed。0.1.0 不生成 force、force-with-lease、ref delete、
自动 pull、merge 或 rebase。

### 16.3 Push postflight

退出码成功后仍需读取远端 ref，只有 OID 等于计划值才 verified。网络中断导致结果
不确定时记录 `unknown`；恢复网络后 verify 远端 OID，再决定 already-applied 或
not-applied，不能盲目重放。

## 17. Release 状态机

### 17.1 Release profile 与 readiness

`.auto-git.toml` 必须显式声明：

- version source 与受控文件；
- allowed branch、version/tag template、Release Commit message；
- full regression 与 build 的 program + argv；
- changelog section、notes source；
- assets glob 的受限项目相对路径和是否必需；
- Provider、remote、draft/prerelease 默认值。

缺少任一必要字段只生成建议，不猜测。readiness 必须验证 clean 状态、允许分支、
upstream 不落后/不分叉、目标版本、变更日志、同名本地/远端 Tag、full regression、
build 和 assets。

### 17.2 有序 checkpoint

```text
release-readiness（只读）
→ release-commit（如需版本/变更日志改动）
→ annotated-tag
→ push-branch
→ push-one-tag
→ github-release
→ release-verify
```

每个写入或公开步骤有独立 plan、hash、审批类与 record。Tag 必须是 annotated Tag，
绑定计划内精确 Commit OID。只 Push 单个目标 Tag，不使用 `git push --tags`。

GitHub Release 使用已经在远端验证存在的 Tag，并使用等价于 `gh release create
<tag> --verify-tag` 的语义；禁止让 Provider 从默认分支自动创建 Tag。Assets 在 plan
中按路径和 SHA-256 固定。

### 17.3 Resume 与冲突

Resume 先重读 HEAD、远端 branch、远端 Tag 和 GitHub Release。与计划完全一致的
checkpoint 标记 already-verified；尚未应用且 preconditions 有效的步骤可重新计划。
同名 Tag/Release 的 OID、notes 或 assets 不一致时 explain-only，不删除、不覆盖、
不 force push。已公开的 branch/Tag 不作为后续失败的自动回滚对象。

## 18. 反馈与基础训练模式

Skill 支持三个反馈层级，安全行为完全一致：

- 新手：解释“现在在哪里、为什么这样选、将发生什么、如何恢复”；
- 标准：结论、文件范围、回归、审批点和下一步；
- 专家：紧凑 JSON/表格、plan hash、pre/post facts。

每次写入前至少显示：动作、精确范围、风险、required regression、恢复入口和需要的
审批。训练内容来自本次真实事实，不编造抽象课程进度。

## 19. 错误与退出码

| 退出码 | 机器码 |
|---|---|
| `0` | success / verified / idempotent replay |
| `2` | invalid_input / schema_error |
| `3` | precondition_failed / drift |
| `4` | approval_missing |
| `5` | regression_failed |
| `6` | git_failed |
| `7` | verification_failed |
| `8` | lock_busy |
| `9` | recovery_unsafe |
| `10` | environment_unsupported / install_failed |
| `11` | auth_required / provider_failed |
| `12` | remote_diverged / non_fast_forward |
| `13` | release_not_ready / release_conflict |

JSON 错误必须包含稳定 code、阶段、可公开摘要和 `retryable`，但不得泄露敏感 diff 或
凭证。

## 20. 测试策略

### 20.1 单元测试

- `SKILL.md` frontmatter、正反触发、渐进披露和 scripts/references 路由；
- `skill.contract.yaml` 的 inputs/outputs/stops/forbidden/approvals/scripts/evaluation；
- porcelain v2/NUL：空格、Unicode、换行、rename、submodule、冲突、unborn/detached；
- canonical JSON、plan hash、path fingerprint 和 drift；
- path escape、literal pathspec、精确 staged set；
- strategy matrix；
- regression trust/timeout/environment；
- lock、原子写、idempotent replay；
- record redaction 和恢复 ownership。
- OS/架构/发行版选择器、installer registry 与权限标记；
- Git config effective value、origin、scope 与邮箱 redaction；
- Remote identity、URL credential redaction、ahead/behind/diverged；
- release version/tag template、asset hash 与 checkpoint 状态机。

### 20.2 集成测试

全部使用临时 Git 仓库，不触碰用户真实仓库：

1. 新目录 init；
2. 功能分支小改动 Commit；
3. 主分支转功能分支；
4. 并行高风险任务选择 Worktree；
5. 脏工作区保护已有改动；
6. 回归失败恢复 index 并阻断 Commit；
7. Commit postflight 与 record 一致；
8. 漂移后旧 plan 拒绝 apply；
9. soft-uncommit 保留文件和 staged 内容；
10. 同一 plan 幂等重放；
11. hook 失败和 Git 锁冲突；
12. 路径含特殊字符；
13. Git 缺失、版本不足、多 PATH 与未知平台；
14. install plan 漂移、PATH 需重启与安装失败；
15. Auto Git Skill 的无 Git安装、宿主发现、升级、卸载与范围隔离；
16. Git identity 缺失、local/global 作用域、origin 与 postflight；
17. GitHub auth 未登录、无账号、账号切换与凭证降级告警；
18. GitHub 空仓库创建与 connect 已有标准 Remote；
19. Remote 非空、名称冲突与身份漂移；
20. 首次 Push 设置 upstream 并验证远端 OID；
21. 后续 Push 的 ahead、behind、diverged、already-synced；
22. Push 网络结果 unknown 后重新 verify；
23. release profile 缺失、版本/Tag/变更日志不一致；
24. full regression/build/assets 失败阻断 Release；
25. Release Commit → annotated Tag → branch Push → Tag Push → GitHub Release；
26. 中断后 resume 跳过已验证 checkpoint；
27. 同名 Tag/Release 冲突时 explain-only。

### 20.3 兼容矩阵

- Agent 宿主：`0.1.0` 至少验证 Codex 与 Claude Code 的 Skill discovery、触发、脚本
  调用和审批反馈；其他兼容 Agent 只在有真实证据时声明支持；
- Python：3.11、3.12、3.13、3.14；
- OS：macOS、Windows、Debian/Ubuntu、Fedora/RHEL；其他 Linux explain-only；
- Git：由 capability test 决定最低版本，不能根据开发机 2.50.1 猜测；
- GitHub CLI：由 capability test 与官方认证状态决定；
- Auto Git Skill 完成安装/发现和零到 GitHub Release 自举；
- 一个普通项目接入并保留原 Git 历史、CI 和开发方式。

## 21. 验收

- [ ] inspect 只依赖机器可读 Git 输出并通过特殊路径 fixture；
- [ ] Auto Git Skill 可被目标宿主发现，正触发命中、反触发不误触发；
- [ ] `skill.contract.yaml` 覆盖副作用、停止点、独立审批、scripts 和高风险测试；
- [ ] install/init/workspace/commit/remote/push/tag/release/recover 均先 plan 后 apply；
- [ ] 修改 plan 或仓库漂移后 apply 被阻断；
- [ ] 仓库中不存在 `git add -A` / `git add .` 执行路径；
- [ ] 回归失败、timeout、缺命令均阻断 Commit；
- [ ] Commit 前失败自动恢复 index；Core 不删除工作区文件，hook 副作用可检测且不覆盖；
- [ ] Commit 后 record 可独立 verify；
- [ ] Auto Git Skill 的无 Git 获取、发现、升级、卸载和范围场景通过；
- [ ] GitHub/Gitee 标准安装源得到相同版本、manifest 与关键文件 hash；
- [ ] 双远程 branch OID 一致；同步 Tag 时两端 Tag target 一致；
- [ ] Python、Git 与 GitHub CLI 的 capability、安装引导和 PATH 场景通过；
- [ ] Git identity 缺失阻断 Commit，local/global 配置和来源可验证；
- [ ] GitHub 登录流程不让 Core 接收或保存 Token；
- [ ] GitHub 仓库创建与 Push 分离，visibility 未显式选择时阻断；
- [ ] 首次/后续 Push 都基于 fetch 后事实，behind/diverged/non-fast-forward 阻断；
- [ ] Push/Tag/Release 都以远端 postflight 为成功依据；
- [ ] Release readiness 覆盖版本、变更日志、full regression、构建、Tag 和 assets；
- [ ] Release Commit、annotated Tag、branch Push、单 Tag Push、GitHub Release 分别审批；
- [ ] GitHub Release 不隐式创建 Tag；
- [ ] Release 中断能幂等 resume，公开资源冲突时不覆盖或删除；
- [ ] recovery 只操作本 record 拥有且未漂移的资产；
- [ ] Skill 不直接执行写入型 Git；
- [ ] 新手反馈能解释策略、影响、审批和恢复；
- [ ] Auto Git 自举场景通过；
- [ ] 普通项目可信场景通过；
- [ ] README 中文/英文入口、语言切换和关键语义一致性通过；
- [ ] 中文用户手册覆盖安装、基本操作、远程、发布、恢复、更新和卸载；
- [ ] OB 发布副本与仓库正文同源，布丁 dry-run/apply/status 证据和真实 Case 状态已记录；
- [ ] GitHub/Gitee 仓库不包含布丁后台 ID、后台 URL 或同步时间；
- [ ] docs、测试证据和外部任务账本按项目门禁对齐。

## 22. 延后到 Backlog

- PR、merge、force push 和自动冲突解决；
- GitLab/Gitee 专用仓库创建、账号和 Release Provider；
- PyPI、npm、容器 Registry 与应用商店发布；
- 通用远程 CI 模板；
- 自动迁移脏改动到 Worktree；
- 后台监控、多仓编排和团队策略中心；
- 完整 Git 训练营；
- root/admin 系统级 Auto Git 安装和单二进制分发；
- Rust 重写或双核心；只有 Python 分发成为真实瓶颈时重新 ADR。

## 23. Spec 确认记录

用户于 2026-08-03 明确要求进入 Go 模式，严格执行 Skill Engineering 开发工程，并在
完成本地实现和完整测试后汇报。本确认允许：

- 接受 ADR 0002；
- 创建可追踪 TDD Plan；
- 在隔离候选中按 RED → GREEN → REFACTOR 实现；
- 使用同一 Native Plan 应用到当前保存项目并做本地验证。

本确认不授权 Commit、Push、创建真实远程仓库、Tag、Release、Global Skill 安装或
对真实项目做破坏性测试；这些动作仍需独立审批。

### 23.1 发行修订确认状态

用户于 2026-08-03 已确认取消自建安装脚本，采用标准 Skill 安装方式，并要求 Auto Git
自身上库到 GitHub 与 Gitee 两个远程仓库。本次确认允许创建和呈现发行 Design、ADR 与
Spec 修订；在用户复核修订后的 Spec 并批准 TDD Plan 前，不写发行实现。创建真实远程
仓库、首次 Commit、两次 Push、Tag 和 Release 仍在各自动作前提供事实预览并分别审批。

用户同日确认：README 必须提供中文和英文两版并在顶部切换；产品必须交付一份完全从
用户视角编写、比 README 更具体的独立中文操作 Playbook，并将受控 OB 发布副本同步到
布丁。该要求已进入 US-025，允许创建上述 TDD Plan并开始本地实现与布丁发布；Git
Commit、远程创建、Push、Tag、Release 和 Global 安装仍需独立审批。

## 24. 参考

- [Python subprocess 官方文档](https://docs.python.org/3/library/subprocess.html)
- [Agent Skills 开放格式](https://agentskills.io/)
- [Skills CLI](https://github.com/vercel-labs/skills)
- [Git 官方安装指南](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Git 官方首次配置指南](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup)
- [Git 官方 Remote 指南](https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes)
- [GitHub CLI 安装](https://cli.github.com/)
- [GitHub CLI 登录](https://cli.github.com/manual/gh_auth_login)
- [GitHub 官方账号创建指南](https://docs.github.com/en/account-and-profile/how-tos/account-management/creating-an-account-on-github)
- [GitHub CLI 创建仓库](https://cli.github.com/manual/gh_repo_create)
- [GitHub CLI 创建 Release](https://cli.github.com/manual/gh_release_create)
- [GitHub Push 指南](https://docs.github.com/en/get-started/using-git/pushing-commits-to-a-remote-repository)
- [Node.js child_process 官方文档](https://nodejs.org/api/child_process.html)
- [Node.js Single Executable Applications](https://nodejs.org/api/single-executable-applications.html)
- [Rust std::process::Command](https://doc.rust-lang.org/stable/std/process/struct.Command.html)
- [Cargo install 官方文档](https://doc.rust-lang.org/stable/cargo/commands/cargo-install.html)
