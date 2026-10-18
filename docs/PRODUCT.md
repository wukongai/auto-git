# Auto Git 产品定义

完整需求分析、User Stories 与逐故事验收条件见
[Auto Git 0.1.0 PRD](PRD.md)。

## 一句话价值

让任何使用 Agent 开发或工作的普通用户，都能在不记忆 Git 命令的情况下，安全、
自动、可解释地完成版本管理，并随实际操作逐步学会 Git。

## 核心问题

普通用户知道“应该保存版本”，但可能连 Git、Auto Git 或 GitHub CLI 都没有安装，
也不知道何时初始化仓库、怎样连接远端、什么时候可以 Push、Tag 和 Release，以及
出错后如何恢复。Agent 虽然能运行命令，却可能忘记提交、误判工作区、混入无关文件
或越过公开发布边界。

Auto Git 把这些判断变成一个可安装的生产级 Agent Skill：根 `SKILL.md` 负责理解、
教学与审批，随 Skill 分发的 `scripts/` 负责读取真实状态、生成不可漂移计划、执行、
验证和恢复。

## 目标用户

- 使用 Codex、Claude Code 或其他 Agent 完成开发的 Git 新手；
- 不想反复提醒 Agent 做版本管理的独立开发者和内容创作者；
- 希望统一多个项目 Git 门禁、审批和回归策略的团队；
- 需要 Git 训练营、教学案例和可复现实操环境的讲师与学员；
- 希望给现有工程增加安全 Git 自动化，而不更换工具链的项目维护者。

## 核心体验

用户可以说：

- “我的电脑还没有 Git，帮我检查并指导安装。”
- “帮我安装 Auto Git，装好后确认可以使用。”
- “帮我把这个新项目纳入 Git 管理。”
- “我改完了，检查一下能不能提交。”
- “这是功能开发，需要分支还是 Worktree？”
- “先跑回归，通过后准备提交。”
- “帮我创建或连接 GitHub 仓库，先不要 Push。”
- “把这个版本 Push 上去。”
- “检查是否满足发布条件，然后发布 `0.1.0`。”
- “帮我恢复上一次修改，但不要丢掉当前文件。”

Auto Git 返回：真实状态、推荐策略、将发生的动作、回归结果、审批点和安全恢复入口。

## 产品形态

Auto Git 的用户产品只有一个：**Auto Git Skill**。它不是“Skill + 另一个需要单独
安装的 Auto Git CLI”，也不是 MCP Server。

Skill 包含：

1. **`SKILL.md`**：自然语言触发、反触发、策略解释、教学、审批和结果反馈；
2. **`skill.contract.yaml`**：输入、输出、停止点、副作用、审批和验证契约；
3. **`scripts/`**：环境诊断、仓库盘点、不可变计划、执行、验证、记录、锁和恢复；
4. **`references/`**：Git、GitHub、安装、Remote、Push、Release 和恢复指引；
5. **`tests/`**：结构、脚本、回归、高风险和真实任务验证用例。

项目配置、hooks、CI 和 Provider 适配是 Auto Git Skill 可选调用的边界资源，不是用户
需要额外安装的第二个 Auto Git 产品。`0.1.0` 采用标准仓库型 Skill 安装、升级和卸载：
GitHub 是主发行仓库与简写安装源，Gitee 是同一 Commit 和版本的完整 Git URL 镜像源。
产品不创建 `install.sh`、`install.ps1` 或私有安装协议。

公开仓库提供中文与英文 README，并交付一份完全从普通用户视角编写的中文用户手册。
仓库手册是公开事实源；同步到布丁时使用 OB 发布副本承载平台元数据，Auto Git 运行时
不依赖布丁。

## 与相关项目的关系

- **ANK**：负责项目工程化初始化和开工体检；可以推荐 Auto Git，但 Auto Git 不依赖
  ANK 运行。
- **Skill Engineering**：Auto Git 的上游开发与治理工具，负责需求恢复、Authoring
  Brief、独立候选、预览、评测、安装审计和版本维护；用户运行 Auto Git 时不依赖它。
- **GitHub/GitLab/Gitee**：标准 Remote 由 Git Core 统一处理；`0.1.0` 先提供 GitHub
  仓库创建、认证检查和 Release 专用适配器，其他 Provider 后续增加。
- **CI**：执行回归的远程环境，不等同于回归测试本身。

## 开源边界

目标是把通用本地核心、Agent Skill、schemas、tests、示例和基础 CI 模板作为独立
开源产品。许可证、品牌、远程 Provider 和托管能力在发布前通过单独 ADR 确认。

## 当前版本不做

- 不后台监控用户所有目录；
- 不未经批准自动 Push、merge、tag 或 Release；
- 不保存 Git 凭证或代管 GitHub 账号；
- 不替代 Git、代码托管平台或项目自己的测试框架；
- 不要求所有任务都使用 Worktree；
- 不在 `0.1.0` 同时覆盖所有 Agent、Provider 和 CI 平台；
- 不自动解决 merge/rebase 冲突，不提供 PR、merge 或包注册表发布；
- 不要求用户额外安装独立 pipx CLI；
- 不把 MCP、常驻服务或 Global 安装设为使用 Auto Git 的前提。
