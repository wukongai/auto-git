# Changelog

本项目遵循语义化版本。尚未正式发布的能力保留在 `Unreleased`。

## [Unreleased]

### 安全修复候选 0.1.0-dev.1

- 精确暂存后执行真实integrity检查；代码或配置变更缺少项目回归时阻断Commit/Push，检查结果进入回执。
- 机器阻断merge/rebase/cherry-pick/revert/bisect、未合并路径、detached HEAD及错误仓库边界。
- Commit后核对实际树、父提交、路径、当时index及可见工作区；Hook越界时保全已有历史并报告核验失败。
- Push计划固定远端目标、OID及将公开提交，写前复核；Tag Push核验绑定原push endpoint。
- 写入前保存running及脱敏目标；失败、部分执行、结果未知可区分，持久错误不保存stderr或完整diff。
- 只按路径阻断凭证形态文件及待公开历史，inspect不为摘要读取其正文；更新能力与安装状态说明。
- 本轮为本地候选验证，不代表真实安装、远端写入或正式发行完成。

### Added

- 按AEF Docs Init完成六领域文档迁移、51目录导航和机器合同，保留产品定义批准状态及审核PDF原件；补齐暂存区凭证/格式提交门禁和4项临时仓库测试，最终117 passed、1 skipped。

- 产品定义0.2六章正文、统一待解决问题、创业与传统经营两版画布及完整8页PDF；2026-10-18用户审核通过，验证父任务与5个子任务完成并同步OB/飞书。
- 2026-10-19 AEF Docs Init检查报告：保留旧工作台，明确新版目录合同与工程门禁缺口；补充产品定义主文专用导出脚本。

- 使用 ANK 初始化跨 Agent 工程化骨架。
- 建立 Auto Git 独立产品、架构、Roadmap、Task、ADR、Sprint 和 Handoff 事实源。
- 建立 `0.1.0` PRD、25 个 User Stories、逐故事验收条件和技术 Spec 追踪关系。
- `0.1.0` 范围扩展为 Git/Auto Git/gh 安装、Remote、Push、annotated Tag 和 GitHub
  Release 的端到端闭环；新增 ADR 0003 固定 GitHub-first Provider 策略。
- 用户确认 Auto Git 是由 Skill Engineering 创建和治理的独立 Skill；新增 ADR 0004，
  把产品形态改为 Skill-first + bundled `scripts/`，独立 pipx CLI 与 MCP 延后。
- 新增根 `SKILL.md`、`skill.contract.yaml`、OpenAI 宿主元数据和安装/安全/工作流/
  Release references。
- 新增 Python 3.11+ 标准库确定性核心：doctor、porcelain v2/NUL facts、canonical
  plan hash、fingerprint 漂移、原子记录、仓库锁、精确 staging、回归、Commit、
  Remote/Push、GitHub adapter、Release readiness/resume、manifest 与恢复。
- 新增统一 `doctor/inspect/plan/apply/verify/recover/resume` 脚本入口、24 项 pytest、
  success/failure/high-risk/holdout 行为案例，以及 local bare remote/fake gh E2E。
- 新增 `verify-mirrors` 只读 CLI：校验 GitHub/Gitee 的 branch OID 与可选 annotated
  Tag target 是否和本地事实一致，缺失或漂移时阻断完成报告。
- 重写用户视角中文 `README.md`，新增英文 `README.en.md` 和顶部语言切换；新增独立
  中文用户 Playbook，覆盖安装、Git 检查、Commit、Remote、Push、Release 与恢复。
- 安装参考改为标准 `npx skills` 生命周期，不再使用自建 Shell/PowerShell 安装器或
  Release ZIP 首装协议。
- 中文用户手册已通过 OB projection 同步到布丁草稿 Case
  `cmscwjpjp00e5pokaitm2t42c`；平台元数据仅保存在 OB，不进入公开仓库。
- fresh 本地回归更新为 99 项 pytest、ruff、compileall 全通过；修订候选继续通过
  Skill Engineering content gate、production review 100/A 与 self-test。
- 独立代码审查后加固恢复与远端边界：恢复必须单独计划和精确审批，备份/当前 index
  checksum 漂移时 fail closed；Remote/分支名拒绝参数注入，fetch 失败阻断，首次
  Push 建立并验证 upstream，双仓 branch/annotated Tag 全矩阵做 postflight。
- GitHub `owner/repo` 与 Tag 名称也在进入 `gh`/Git argv 前验证，拒绝选项注入、路径
  穿越和无效 ref。
- Remote URL 在 plan 前拒绝 user-info、query、fragment 和疑似凭证，operation record
  只保存脱敏仓库身份；GitHub 认证固定 account/protocol，建仓后回读 Owner/name/
  visibility/URL。
- 新增项目 `.auto-git.toml` Release profile；readiness 验证允许分支、fetch/upstream、
  Tag 冲突、回归、构建和必需 assets。Release resume/创建/verify 严格比较 annotated
  Tag object/target，并回读 GitHub Release 正文、标题、状态、target、URL 和 assets。
- operation record 按 action 重读机器事实；未知 action 返回 unknown。恢复采用临时文件、
  fsync、checksum 与原子替换。计划新增参数 schema、风险、postconditions、恢复说明和
  expiry；argparse 失败也遵循 JSON 错误合同。
- CLI 增加 dependency/auth/release/history 与受管恢复入口；`--json` 的成功和失败
  输出均稳定且脱敏。收窄 Claude allowlist，不再自动放行 Git 写入和通用运行时。
- 完成 ANK `.new` 逐文件差异审计：保留用户 Constitution/Product/文档地图，清理
  活跃 Claude settings、rules 和 commands 的运行占位符，并保留 `.new` 非覆盖证据。
- 依据标准 Skills CLI 官方源码修正首装自举：普通 GitHub/Gitee 仓库安装需要 Git；
  无 Git 新手先由宿主 Agent + 系统官方入口准备 Git，再标准安装 Auto Git。中英
  README、用户 Playbook、Skill 入口、Spec/ADR 和布丁 draft 已同步修正。
- Skill Engineering production creation review 100/A；最终 Native Plan fingerprint
  `c94d0611…a5fc0` 已 apply/verify/self-test。
- 已初始化本地Git仓库，2026-10-18旧版基线提交7b2f8b7已推送GitHub；尚未创建Tag或Release。
