# Auto Git 文档地图

## 产品事实源

- 已审核产品定义0.2：[主文](PRODUCT.md)、[待解决问题](product-questions.md)、[完整8页PDF](../output/pdf/auto-git-product-definition-v0.2-reviewed.pdf)、[两版画布](references/product-definition-0.2-charts/canvases.html)。
- [2026-10-19文档初始化检查](research/2026-10-19-aef-docs-init-audit.md)：旧工作台可用，新版六领域结构尚未迁移。

- [`PRODUCT.md`](PRODUCT.md)：目标用户、价值、边界和产品形态。
- [`PRD.md`](PRD.md)：`0.1.0` 需求分析、User Stories 和逐故事验收条件。
- [`constitution.md`](constitution.md)：跨版本不可妥协原则。
- [`ARCHITECTURE.md`](ARCHITECTURE.md)：分层、组件职责、审批和依赖方向。
- [`ROADMAP.md`](ROADMAP.md)：版本规划和发布边界。
- [`TASK.md`](TASK.md)：当前任务。
- [`BACKLOG.md`](BACKLOG.md)：未进入当前版本的候选。
- [`research/2026-08-03-ank-new-diff-audit.md`](research/2026-08-03-ank-new-diff-audit.md)：ANK `.new` 非覆盖差异与 adopt/adapt/reject 结论。
- [`superpowers/specs/2026-08-02-auto-git-v0.1.0-spec.md`](superpowers/specs/2026-08-02-auto-git-v0.1.0-spec.md)：安装到 GitHub Release 的技术契约。
- [`adr/0003-zero-to-release-github-first.md`](adr/0003-zero-to-release-github-first.md)：0.1.0 范围与 GitHub-first 决策。
- [`adr/0004-skill-first-product-and-authoring-boundary.md`](adr/0004-skill-first-product-and-authoring-boundary.md)：Auto Git Skill 产品形态与 Skill Engineering 开发治理边界。

## 当前恢复入口

- [`superpowers/handoff/2026-08-02-auto-git-product-foundation-handoff.md`](superpowers/handoff/2026-08-02-auto-git-product-foundation-handoff.md)

Auto Git Skill 由 Skill Engineering 治理；功能工作遵循
`Product/PRD → Spec → 用户确认 → TDD Plan → 独立候选 → verification → docs/task sync`。
Superpowers/TDD 是实现阶段的内部方法，不建立第二套并行顶层流程。重大跨版本选择
进入 `adr/`，每日事实进入 `logs/daily/`。



This directory is the project operating desk. Keep durable decisions, daily execution logs, sprint plans, specs, handoffs, research, and user-facing guides here so agents and humans can reconstruct context without rereading chats.

## Map

| Path | Purpose | Required when |
|---|---|---|
| `constitution.md` | Durable project principles and non-negotiables | Project initialization and principle changes |
| `dailylog/` | Compatibility daily work log path | Any meaningful work session |
| `logs/daily/` | Standard daily work log path | Any meaningful work session |
| `logs/weekly/` | Weekly summaries and operational reports | Weekly review or recurring operations |
| `sprints/` | Sprint goals, scope, review, and retro | Multi-day project push |
| `superpowers/specs/` | Feature specs and design contracts | New feature, new workflow, architecture change |
| `superpowers/plans/` | Implementation plans and task breakdowns | Feature-level work before coding |
| `superpowers/handoff/` | Cross-session handoff and recovery notes | Pausing, delegating, or switching agents |
| `superpowers/designs/` | Product/UI/interaction design options | UI, UX, or workflow design change |
| `superpowers/testing/` | Test plans, cases, and verification reports | Feature-level or regression-prone work |
| `superpowers/mockups/` | Feature-specific mockups and prototypes | Visual review or design comparison |
| `superpowers/brainstorming/` | Structured ideation and option exploration | Ambiguous product or technical exploration |
| `adr/` | Architecture decision records | Irreversible or high-cost technical choices |
| `backlog/` | Candidate tasks and unscheduled ideas | Not ready for current sprint |
| `research/` | External/internal research and evaluation notes | Tool/model/vendor/approach comparison |
| `guides/` | How-to guides and operating manuals | Repeatable human or agent workflow |
| `tutorials/` | Step-by-step learning material | Teaching or onboarding a workflow |
| `engineering/` | Durable technical and harness notes | Architecture, runtime, safety, or toolchain design |
| `playbook/` | Operational runbooks and recovery procedures | Repeated high-risk or high-frequency operation |
| `onboarding/` | New machine/user setup | Environment or agent setup |
| `releases/` | Release notes, evidence, and rollback path | Versioned shipping event |
| `sync/` | OB task / external board sync notes | Project task state must align outside repo |
| `references/` | Supporting materials and source artifacts | Non-authoritative source material |
| `mockups/` | Global visual prototypes | Cross-feature visual artifacts |
| `migration/` | Data/code migration audits and rollout notes | Migration, split, import, or compatibility work |

## Naming

- Daily log: `YYYY-MM-DD.md`
- Sprint: `YYYY-MM-DD-sprint-<slug>.md`
- Spec: `YYYY-MM-DD-<slug>-spec.md`
- Plan: `YYYY-MM-DD-<slug>-plan.md`
- Handoff: `YYYY-MM-DD-<slug>-handoff.md`
- ADR: `YYYY-MM-DD-<slug>.md`
- Release: `<version>.md` or `YYYY-MM-DD-<version>.md`
- Engineering note: `YYYY-MM-DD-<slug>.md`

## Completion Rule

A task is not done until the matching docs are updated. For feature-level work, update the spec or plan, test plan, daily log, and handoff if the work will continue later.
If the project uses OB task or an external board, closeout is not done until that task record is updated or a sync failure is explicitly reported.
