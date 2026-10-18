# Auto Git 文档初始化检查

日期：2026-10-19。范围：提交已获批准的产品定义0.2、PDF和日志前，检查文档初始化；不执行全库迁移。

## 结论

旧版ANK/AEF工作台主要目录与真实业务文档齐全，可继续保存本次交付；不能宣称已完成新版AEF Docs Init六领域初始化。现有产品定义获批与文档体系升级是两件事。

| 检查 | 结果与证据 |
|---|---|
| 原有文档工作台 | constitution、产品/PRD、架构、任务、路线图、日志、Sprint、Spec/Plan/Handoff、ADR、研究、教程、sync等存在 |
| 原有模板dry-run | 旧兼容脚本只读预览：保留现有正文；新版lifecycle模板缺失，部分模板不同 |
| 新版Docs Init检查 | `docs_init.py --target . --check`返回blocked，已有docs/README.md差异，written为空 |
| 新版机器合同与目录 | `.aef/docs-layout.json`不存在；product/project/business/customer-success/knowledge六领域结构尚未完整建立 |
| 历史.new文件 | 2026-08-03已有逐项adopt/adapt/reject审计，保留为证据，不当作活跃入口 |
| 配置事实 | `.ai-native/profile.json`已补真实GitHub地址；生成入口AGENTS.md中的旧远程描述留待后续adapter升级统一处理 |
| 工程门禁 | `.git/hooks/pre-commit`和本项目credential-lint.sh缺失；不宣称硬门禁已安装，本轮提交前单独执行凭证扫描 |
| Skill分发 | profile声明skillhub_enabled=false，跳过skillhub对账 |
| 产品验收 | PRODUCT为approved，Q-005已关闭；完整8页PDF保留用户审核时原件，草稿页脚为历史导出状态 |
| 外部任务 | 前次已核验Definition父任务与5个子任务、初始化定义任务全部Done，关系保留 |

本次修正文档地图、Task与Changelog的过期状态，不改宪法或迁移原路径。新版初始化应另行按逐文件迁移预览、外部备份及批准后的同一方案执行，避免覆盖现有导航与审批记录。

## 使用工具

检查采用本机AEF源码中的`skills/aef-docs-init`（Python标准库CLI）；旧兼容预览来自ai-native-kit的`aef-docs-init`。两次检查均为只读，没有apply或新增新布局文件。

## 提交范围

包含已审核产品定义、问题记录、审阅证据、画布源数据与SVG/PNG/HTML、最终reviewed PDF/HTML、导出脚本和相关日志/导航。中间版PDF/HTML留本地，不加入此次提交。PDF的本机附件链接仍为本机引用，GitHub阅读正文请使用docs中的相对链接。
