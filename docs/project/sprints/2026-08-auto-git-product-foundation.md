# Sprint：Auto Git Product Foundation

状态：Doing — local distribution candidate verified; public Git release approvals pending

日期：2026-08-02 起

OB Task：
`/Users/aim5/Documents/OB/04 Inbox/task/2026-08-02-【Auto Git】Auto Git 0.1.0 Skill 产品开发.md`

## 目标

建立由 Skill Engineering 治理的独立 Auto Git Skill 工程，固定开发期与运行时依赖
边界，完成 `0.1.0` 实现前的只读能力盘点、技术选型、Spec、必要 ADR 和 TDD Plan。

## 进入范围

- ANK 工程骨架与非敏感 profile；
- 本地 Git 仓库；
- Product、Constitution、Architecture、Roadmap、Backlog、Task、ADR 和 Handoff；
- 本机已有 Git 能力只读盘点；
- Skill-first 产品结构、`0.1.0` 技术选型与 Spec/Plan。
- 标准 Skill 安装、GitHub 主源、Gitee 同提交镜像与双远程发行修订。
- README 中英双版、中文用户手册与 OB→布丁发布边界。

## 不进入范围

- Auto Git 自身的真实 Commit、Push、远程仓库创建、tag 或 Release；
- ANK 运行时集成、MCP 和独立 CLI；
- 实际用户级/Global 安装；
- 后台守护进程和云服务。

## 验收

- [x] 独立目录和本地 Git 仓库存在；
- [x] 产品事实源和唯一 Handoff 可恢复；
- [x] 依赖方向由 ADR 0001 固定；
- [x] ANK `.new` 差异逐文件审计完成；活跃 Claude 入口无未解释运行占位符，
  用户 Constitution/Product/文档地图未被覆盖；
- [x] Codex 专属任务已调度；
- [x] 只读盘点完成；
- [x] `0.1.0` PRD、User Stories 和逐故事验收条件已形成 Proposed 文档；
- [x] 用户确认 0.1.0 采用安装到 GitHub Release 的端到端方案 A；
- [x] 安装、Remote、Push、Release 和 resume 已进入修订后的 PRD/Spec；
- [x] 用户确认 Auto Git 是由 Skill Engineering 创建的独立 Skill；
- [x] Skill-first、bundled scripts 和无 Git 获取路径已进入修订后的 PRD/Spec；
- [x] `0.1.0` Spec 经用户确认；
- [x] TDD Plan 已创建；
- [x] 隔离候选、实现和本地完整验证通过；
- [x] 同一候选内容应用到保存项目并完成收尾对齐；
- [x] 当前宿主临时普通项目真实样本通过；
- [x] 用户确认取消自建安装器，采用标准 Skill 安装和 GitHub/Gitee 双远程发行；
- [x] 用户复核发行 Design、ADR 0005 与 Spec 修订；
- [x] 用户复核 US-025 双语 README、用户手册与布丁同步验收；
- [x] 创建标准安装、双远程发行与用户文档 TDD Plan；
- [x] 执行 TDD Plan，完成双语 README、用户手册、布丁 draft 同步和双远程本地校验；
- [x] 完成最终安全审查整改与 38 文件 Native Plan/纯 Skill 候选验证；
- [ ] 首次 Commit、真实双 Remote/Push/Tag/Release 与跨宿主安装试用经独立审批完成。
