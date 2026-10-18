# Auto Git 目标架构

本文件固定当前已确认的产品边界。Auto Git 是由 Skill Engineering 创建和治理、由
用户独立安装的 Agent Skill。实现语言、脚本入口和 schema 细节必须在 `0.1.0`
Spec/Plan 与必要 ADR 中确定。

## 产品与开发关系

```text
Skill Engineering（开发期）
    └── 创建、预览、评测、维护 → Auto Git Skill

用户 / Agent（运行期）
    └── 调用 Auto Git Skill
            ├── SKILL.md：意图、解释、教学、审批
            ├── scripts/：doctor → plan → apply → verify → recover
            ├── references/：安装与 Git 工作流知识
            └── tests/：结构、回归和高风险证据
                    ↓
              标准 Git / Git Remote / GitHub CLI
```

## 组件职责

### 根 `SKILL.md`

- 识别 install、doctor、init、status、workspace、commit、remote、push、release、
  recover、learn 等意图；
- 把普通用户语言翻译为确定性核心参数；
- 解释 branch、Worktree、Commit、Push、CI 和回退；
- 展示影响并请求必要审批；
- 不解析 Git porcelain 文本后自行修改仓库；
- 不要求用户先安装另一个 Auto Git CLI。

### `scripts/` Deterministic Core

- 检测 OS、架构、Git、Python、GitHub CLI、PATH 和 capability，不从聊天猜环境；
- 读取机器可解析的 Git 状态、仓库根、分支、Worktree、index、remote 和冲突；
- 生成带仓库指纹和预期状态的不可变计划；
- 显式限定变更范围，禁止默认 `git add -A`；
- 调用项目回归配置并保存脱敏结果；
- 执行批准的 Git 动作，再验证实际状态；
- 生成可审计记录和安全恢复建议；
- 不保存凭证，不调用模型 Provider。

当前 `0.1.0` 模块：

| 模块 | 责任 |
|---|---|
| `schema.py` / `state.py` / `runner.py` | canonical JSON/hash、原子状态、锁、argv-only 子进程 |
| `doctor.py` / `install.py` / `manifest.py` | capability、依赖/Skill 生命周期计划、归档 SHA-256 |
| `git_facts.py` / `planner.py` | porcelain v2/NUL facts、fingerprint、immutable plan |
| `regression.py` / `executor.py` | 回归、二次漂移检查、精确 staging、Commit 和 operation record |
| `remote.py` / `github.py` | 标准 Remote/fetch/Push postflight 与 GitHub CLI adapter |
| `release.py` / `recovery.py` | readiness、Tag/Release checkpoint、resume 与所有权恢复 |
| `cli.py` / `auto_git.py` | `doctor/inspect/dependency-plan/auth-status/plan/apply/verify/plan-recover/recover/release-check/resume/verify-mirrors/history` 薄入口 |

Release readiness 从项目 `.auto-git.toml` 读取显式 profile；缺失版本源、允许分支、
upstream/Remote、回归、构建、必需资产或 Tag 事实时 fail closed。GitHub Release
创建前验证本地/远端 annotated Tag object 与 target，创建后再回读 Release 状态。

计划和 record 默认位于用户状态目录，不应写入被操作仓库；否则它们会正确触发
fingerprint 漂移。

### Skill Distribution 与 Installer Adapter

- 用户安装的是 Auto Git Skill；安装范围由宿主能力明确为 project、profile 或 global；
- `0.1.0` 使用标准 Skills CLI 或宿主原生 Skill 管理器安装、升级和卸载；
- GitHub 是主发行仓库和简写安装源；Gitee 是相同 Commit、版本与 manifest 的完整
  Git URL 镜像源；
- 不创建 `install.sh`、`install.ps1` 或 Auto Git 私有安装器；
- 已从标准 Skills CLI 官方源码确认普通 GitHub/Gitee 仓库安装走 Git clone；没有
  Git 且 Auto Git 尚未安装时，先由宿主 Agent + 系统官方入口准备并验证 Git；
- Auto Git 安装后才由自己的 doctor 接管依赖检查，不假装未安装的 Skill 可以先运行；
- 按 macOS、Windows、Debian/Ubuntu、Fedora/RHEL 生成 Git 与 GitHub CLI 安装计划；
- 计划固定官方来源、包管理器、命令参数、是否需要管理员权限和安装后验证；
- 密码、系统弹窗、浏览器登录和 Token 输入始终交给操作系统或官方工具；
- 未识别平台只提供官方链接与 explain-only 指引，不拼接未知安装命令。

### Project Adapter

- 描述保护分支、允许的工作区策略、回归档位、版本来源、变更排除、构建产物和发布边界；
- 接入现有测试命令、hooks 与 CI，不强迫项目更换工具链；
- 配置默认进入项目仓库，敏感值只留用户层。

### Provider / CI Adapter

- 标准 Git Remote 负责已有远端的连接、fetch、Push 和 Tag Push；
- `0.1.0` GitHub Adapter 通过官方 GitHub CLI 检查认证、创建仓库和创建 Release；
- Auto Git 自身以 `origin`（GitHub）和 `gitee`（Gitee）双远程发布，并用 branch OID
  与 Tag target 一致性证明镜像同步；
- Gitee 镜像继续走标准 Git Core，不等同于新增 Gitee Provider Adapter；
- 后续封装 GitLab、Gitee 等账号、仓库与 Release API 差异；
- remote create/connect、Push、tag、Release 保持独立计划、记录和审批；
- CI 模板只复用项目已定义的回归，不重新发明测试真相源。

### User Documentation / Pudding Projection

- `README.md` 与 `README.en.md` 是仓库中文/英文入口；
- `docs/knowledge/users/guides/auto-git-user-manual.zh-CN.md` 是公开中文用户手册事实源；
- OB `_OB工程/publications/auto-git/Auto Git 用户手册.md` 是布丁发布 projection；
- projection 只增加布丁所需公开 frontmatter，正文与产品版本必须可校验同源；
- `pudding_id`、后台 URL 和同步时间只保存在 OB，不进入 GitHub/Gitee；
- 布丁同步是发行文档动作，不是 Auto Git Skill 运行时依赖。

## 从 Skill 安装到发布的数据流

```text
安装并发现 Auto Git Skill
→ doctor 检测 Git / gh / PATH / auth
→ 缺失依赖安装计划与验证
→ Git identity / scope 首次配置
→ init / workspace / Commit
→ remote create 或 connect
→ fetch + ahead/behind + Push plan
→ release readiness
→ 版本/变更日志/构建/Release Commit
→ annotated tag
→ Push branch
→ Push tag
→ GitHub Release（校验远端 Tag）
→ postflight / record / resume
```

任一步失败都停止后续动作。已成功的公开动作不通过删除、force push 或改写 Tag
“回滚”；系统保存 checkpoint，重新读取远端事实后提供继续、修复或 explain-only。

## 工作区策略

- 非 Git 目录：只读说明影响，批准后才 `git init`。
- 干净功能分支、小改动：允许当前分支。
- `main/master`、脏工作区、并行任务、重构或高风险：优先新分支/Worktree。
- Worktree 是风险策略，不是所有任务的强制仪式。
- 当前用户改动永远视为需保护资产，不自动覆盖、清理或丢弃。

## 审批模型

| 动作 | 默认 |
|---|---|
| inspect / status / diff summary | 自动只读 |
| 回归测试 | 可自动执行项目已授权命令 |
| 安装/升级/卸载 Auto Git Skill | 展示来源、版本、宿主、范围、diff 和撤销方式后批准 |
| 安装 Python / Git / GitHub CLI | 展示来源、命令、权限和验证后批准 |
| init / branch / Worktree | 展示计划后批准 |
| stage / Commit | 展示精确文件和信息后批准 |
| 创建或修改 Remote / 创建 GitHub 仓库 | 分别展示可见性、Owner、名称和 URL 后批准 |
| Push | 本地验证通过后单独批准 |
| tag / Release | 分别批准；Release 不得隐式创建 Tag |
| merge / PR / 包注册表发布 | `0.1.0` 不执行 |
| reset / clean / force push / 删除 | 备份、风险说明、明确批准 |

## 依赖方向

Auto Git 运行时不依赖 ANK 或 Skill Engineering。Skill Engineering 在开发期读取
Auto Git 的 Product、Spec、contract 和测试证据，生成并维护独立候选；它不是 Auto Git
运行时 delegate。ANK 和其他项目可通过稳定 Skill/JSON 接口消费 Auto Git。MCP 与
独立 CLI 均不进入 `0.1.0`，未来如有明确需求再作为适配器评估。
