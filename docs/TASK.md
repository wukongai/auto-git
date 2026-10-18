# 当前任务

当前版本：`0.1.0-dev.0`

当前状态：Local 0.1.0 candidate verified; publication approval pending

外部任务账本：
`/Users/aim5/Documents/OB/04 Inbox/task/2026-08-02-【Auto Git】Auto Git 0.1.0 Skill 产品开发.md`

## Product Foundation

- [x] 使用 ANK 初始化跨 Agent 工程化骨架。
- [x] 初始化独立本地 Git 仓库，默认分支为 `main`。
- [x] 固定 Auto Git 与 ANK、Skill Engineering 的独立仓库和运行时边界。
- [x] 用户确认 Auto Git 是由 Skill Engineering 创建和治理的独立 Skill。
- [x] 建立 Product、Constitution、Architecture、Roadmap、Backlog、ADR、Sprint、
  Daily Log 和唯一 Handoff。
- [x] 完成 ANK profile 回填后的 `.new` 差异审计；保留用户 Constitution/文档地图，
  合并活跃 Claude 入口所需值并记录 adopt/adapt/reject。
- [x] 在 Codex 创建 Auto Git 专属任务并从唯一 Handoff 开工。

## `0.1.0` Discovery

- [x] 只读盘点本机已有 Git Skill、脚本、hooks、CI 模板和项目约定。
- [x] 比较 Python、Node.js、Rust 或最小脚本核心的安装与跨平台取舍。
- [x] 在 Proposed Spec 中定义 Skill/Core、配置、状态、锁、审批和恢复契约。
- [x] 创建 Proposed `0.1.0` Spec。
- [x] 创建 Proposed `0.1.0` PRD，补齐需求分析、User Stories 和逐故事验收条件。
- [x] 创建 Proposed ADR 0002，等待 Spec 一并确认。
- [x] 用户确认方案 A：`0.1.0` 覆盖安装到 GitHub Release 的端到端纵向闭环。
- [x] 扩展 PRD 为 24 个 User Stories，并补齐 Git/Auto Git/gh 安装、Git identity、Remote、Push、
  Release 与 resume。
- [x] 创建 Accepted ADR 0003，固定 Provider-neutral Core + GitHub 首适配器。
- [x] 创建 Accepted ADR 0004，固定 Skill-first 产品形态与开发期治理边界。
- [x] 把 PRD、Spec、Architecture、Roadmap 和 Handoff 全部改为 Skill-first。
- [x] 用户确认 PRD 与 Spec。
- [x] 使用 Skill Engineering 保存 Native Authoring Brief。
- [x] 创建逐 Story/AC 可追踪的 TDD Plan。
- [x] 在隔离候选中按 TDD 实现 Auto Git Skill。
- [x] 通过单元、临时仓库集成、行为、高风险和 Skill Engineering 门禁。
- [x] 应用同一候选并完成 fresh 全量复验和文档对齐。
- [x] 用当前宿主 Agent 完成临时普通项目 inspect → plan → exact Commit → verify。
- [x] 用户确认标准 Skill 安装方式，取消自建 Shell/PowerShell 安装器。
- [x] 用户确认 Auto Git 采用 GitHub 主源 + Gitee 同提交镜像的双远程发行。
- [x] 用户复核双远程发行 Design、ADR 0005 与 0.1.0 Spec 修订。
- [x] 用户复核 README 中英双版、中文用户手册与布丁发布验收。
- [x] 创建标准安装、双远程发行与用户文档 TDD Plan。
- [x] 按 TDD 完成本地双远程 branch OID/annotated Tag 一致性、缺失 ref 阻断与
  `verify-mirrors` CLI；真实 GitHub/Gitee postflight 留在发布审批阶段。
- [x] 编写并验证 `README.md`、`README.en.md` 与中文用户手册。
- [x] 创建 OB 用户手册发布副本，完成布丁 dry-run/apply，真实 draft Case 已创建。
- [x] 完成独立审查整改：GitHub 目标绑定、Release resume、幂等重放、锁内二次校验、
  完整 fingerprint 和 stale lock 诊断。
- [x] 生成最终 38 文件 Native Plan，apply/verify 通过，纯 Skill 候选 91 项测试通过。
- [ ] 如需面向公网正式发布，在布丁完成 published 状态并验证公开 URL。
- [ ] 经独立审批完成 Auto Git 自身首次 Commit、真实远程 Push、Tag、Release 和安装试用。

## 当前禁止

- 不执行 Commit、Push、创建真实远程仓库、tag 或 Release；
- 不实际安装 Auto Git、Git、GitHub CLI 或 Global Skill；
- 不把 ANK 或 Skill Engineering 变成 Auto Git 运行时依赖；
- 不创建独立 pipx CLI 或 MCP Server；
- 不从聊天猜测 Git 仓库状态。
