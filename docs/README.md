# 项目文档总导航

本目录存放下表对应材料；按类型选择正文位置，避免重复维护。

Product 记录产品事实和演进方向；Project 记录执行安排。发布归 product/releases，发布任务归 project/tasks。
产品五类产物：产品定义（product-definition.md）、用户与市场研究（research）、Epic/用户故事（requirements）、故事地图（story-map.md）、迭代计划（project/sprints）。
定位是产品定义的一部分，定义还包含用户、价值、商业画布与指标；同一事实只维护一份正文。已有正文先读并审阅增量，职责冲突时保留原文并确认处理方案。
点子先记 product/ideas.md；明确用户、价值与验收后形成 requirements/<需求名>/story.md，需求背景写入同一故事。详细调研归 product/research。
PRD 组织多个故事的产品方案，不要求每个故事另写 PRD。story-card.json 是按需机器接口，不要求人工重复维护。
Project 看板入口为 board.md，需求池、待办、进行中、待验收、已完成是状态；具名待办正文归 tasks，状态流转不搬文件。
任务卡或已采用的外部看板为状态唯一来源；board.md 仅作视图或链接入口，不再手工复制状态。日报、周报归 logs，以 -daily.md、-weekly.md 区分。
CHANGELOG 记录 Unreleased 和工程版本变化，不写任务进度。Plan 写技术步骤并引用任务 ID；Sprint 承载本轮目标、故事承诺、依赖与结果，可引用执行任务，Sprint 和日报不复制任务状态。
生命周期周期、版本和 Sprint 分开；阶段文档不冒充批准，机器阶段状态仍在 `.aef/lifecycle/<周期>/manifest.json`。
变更包 spec 是拟议规格；验证和评审通过后更新生效规格。debug 加 diagnosis，优化加 optimization。
通用部署/回滚手册在 engineering/maintenance/runbooks；具体版本回滚证据在 product/releases。
Wiki 以 knowledge/README 为入口；用户指南正文唯一保存于 knowledge/users，运营只引用。
学习记录讲学到什么；日报讲做了什么。产品调研与技术选型实验分开。
本文档初始化一次建立全部静态分类；带尖括号的路径是未来实例，不创建字面占位目录。
凭证、真实客户明细和工程运行日志不进入文档仓。测试代码不放 docs。旧资料保留，迁移另行评审。
目录存在只说明分类就绪，不说明产品文档已写、阶段已批准或版本已发布。

| 文档类型 | 路径 |
|---|---|
| 导航 | `docs/README.md` |
| 项目原则 | `docs/constitution.md` |
| 产品定义 | `docs/product/product-definition.md` |
| 故事地图 | `docs/product/story-map.md` |
| 路线图 | `docs/product/roadmap.md` |
| 产品调研 | `docs/product/research/` |
| 点子 | `docs/product/ideas.md` |
| 需求发现 | `docs/product/requirements/<需求名>/story.md` |
| 用户故事 | `docs/product/requirements/<需求名>/story.md` |
| 故事卡 | `docs/product/requirements/<需求名>/story-card.json` |
| 产品需求文档 | `docs/product/prd/` |
| 发布导航 | `docs/product/releases/README.md` |
| 变更日志 | `docs/product/releases/CHANGELOG.md` |
| 发布记录 | `docs/product/releases/<版本>/release.md` |
| 发布说明 | `docs/product/releases/<版本>/release-notes.md` |
| 发布验证 | `docs/product/releases/<版本>/verification.md` |
| 版本回滚 | `docs/product/releases/<版本>/rollback.md` |
| 看板 | `docs/project/board.md` |
| 待办 | `docs/project/board.md` |
| 任务 | `docs/project/tasks/` |
| 迭代 | `docs/project/sprints/` |
| 生命周期 | `docs/project/lifecycle/<周期>/` |
| 风险 | `docs/project/risks.md` |
| 会议 | `docs/project/meetings/` |
| 日报 | `docs/project/logs/` |
| 周报 | `docs/project/logs/` |
| 交接 | `docs/project/handoffs/` |
| 工程导航 | `docs/engineering/README.md` |
| 架构 | `docs/engineering/architecture/` |
| 技术选型实验基线 | `docs/engineering/research/` |
| 架构决策 | `docs/engineering/adr/` |
| 生效规格 | `docs/engineering/specs/<能力名>/spec.md` |
| 变更提案 | `docs/engineering/changes/<变更名>/proposal.md` |
| 变更设计 | `docs/engineering/changes/<变更名>/design.md` |
| 拟议规格 | `docs/engineering/changes/<变更名>/spec.md` |
| 技术计划 | `docs/engineering/changes/<变更名>/plan.md` |
| 测试设计 | `docs/engineering/changes/<变更名>/testing.md` |
| 验证证据 | `docs/engineering/changes/<变更名>/verification.md` |
| 评审 | `docs/engineering/changes/<变更名>/review.md` |
| 变更附件 | `docs/engineering/changes/<变更名>/assets/` |
| 诊断 | `docs/engineering/changes/<变更名>/diagnosis.md` |
| 优化 | `docs/engineering/changes/<变更名>/optimization.md` |
| 接口 | `docs/engineering/api/` |
| 数据 | `docs/engineering/data/` |
| 规范 | `docs/engineering/standards/` |
| 环境 | `docs/engineering/maintenance/environment/` |
| 操作部署回滚手册 | `docs/engineering/maintenance/runbooks/` |
| 监控 | `docs/engineering/maintenance/monitoring/` |
| 事故 | `docs/engineering/maintenance/incidents/` |
| 迁移 | `docs/engineering/maintenance/migrations/` |
| 商业化 | `docs/business/commercialization.md` |
| 定价 | `docs/business/pricing.md` |
| 内容规划 | `docs/business/marketing/content-plan.md` |
| 活动 | `docs/business/marketing/campaigns/` |
| 营销素材 | `docs/business/marketing/materials/` |
| 销售手册 | `docs/business/sales/playbook.md` |
| 销售问答 | `docs/business/sales/faq.md` |
| 销售模板 | `docs/business/sales/templates/` |
| 商业指标 | `docs/business/metrics/` |
| 内测 | `docs/customer-success/beta/` |
| 客户接入 | `docs/customer-success/onboarding/` |
| 客户运营 | `docs/customer-success/engagement/` |
| 客户反馈 | `docs/customer-success/feedback/` |
| 客户支持 | `docs/customer-success/support/` |
| 客户复盘 | `docs/customer-success/reviews/` |
| 知识入口 | `docs/knowledge/README.md` |
| 团队入职 | `docs/knowledge/team/onboarding/` |
| 团队学习 | `docs/knowledge/team/learning/` |
| 团队教程 | `docs/knowledge/team/tutorials/` |
| 原理解释 | `docs/knowledge/team/explanations/` |
| 用户入门 | `docs/knowledge/users/getting-started.md` |
| 用户指南 | `docs/knowledge/users/guides/` |
| 用户问答 | `docs/knowledge/users/faq.md` |
| 参考资料 | `docs/knowledge/references/` |
