# Auto Git 0.1.0 Skill 实施计划

状态：Executed locally（24 passed；production review 100/A；真实发布待独立审批）

> **执行要求：** 使用 Skill Engineering Native Authoring + Superpowers TDD。每个生产
> 行为先运行对应失败测试，观察 RED 后再写最小实现；Apply 前使用同一 Authoring Brief、
> candidate、target 和 Native Plan。

**目标：** 交付一个可被 Agent 发现的 Auto Git 生产级 Skill，在不接收凭证、不猜测
仓库事实的前提下，覆盖环境检查、初始化、精确 Commit、Remote/Push、GitHub Release
和所有权感知恢复。

**架构：** 根 `SKILL.md` 负责触发、解释、教学和审批；`scripts/auto_git/` 只通过参数
数组调用 Git/gh，输出版本化 JSON。所有写操作采用 inspect → immutable plan →
approval → drift/lock → apply → postflight → record；网络与公开动作按阶段独立审批。

**技术栈：** Python 3.11+ 标准库运行时、pytest、ruff、Git、fake gh、本地 bare remote、
Skill Engineering portable gates。

---

## 追踪约定

- PRD 验收条件以 `US-xxx/AC-xxx-nn` 标识。
- 所有危险或联网测试只使用临时目录、本地 bare remote 和 fake `gh`。
- 不测试真实凭证、真实远程写入、系统安装、Global Skill 安装。
- 每批完成后运行该批测试；最终重新运行全量验证，旧输出不能替代新证据。

## Task 1：Skill 契约与行为基线

**产物：**

- `SKILL.md`
- `skill.contract.yaml`
- `agents/openai.yaml`
- `references/install.md`
- `references/workflow.md`
- `references/safety.md`
- `references/release.md`
- `tests/self-test.json`
- `tests/skills/auto-git/cases/*.yaml`

**步骤：**

1. 建立成功、失败、高风险和 holdout 行为案例，先证明候选缺失时结构/行为门禁失败。
2. 写最小 Skill 契约，使触发、反触发、审批、解释和脚本委托边界通过。
3. 运行 content gate 与 creation review，保留仍待代码满足的失败证据。

**覆盖：** US-011、US-012、US-013、US-016；AC-011-01..06、AC-012-01..06、
AC-013-01..06、AC-016-01..06。

## Task 2：JSON 契约、命令运行器、状态目录与锁

**产物：**

- `scripts/auto_git/schema.py`
- `scripts/auto_git/runner.py`
- `scripts/auto_git/state.py`
- `scripts/auto_git/redaction.py`
- `tests/unit/test_schema.py`
- `tests/unit/test_runner.py`
- `tests/unit/test_state.py`

**步骤：**

1. 先写 canonical JSON/hash、argv-only runner、脱敏、原子写和互斥锁失败测试。
2. 观察模块缺失/断言失败的 RED。
3. 实现最小代码，覆盖并发锁、超时、命令缺失、输出脱敏和 schema version。
4. 重构公共错误类型，保持运行时仅依赖标准库。

**覆盖：** AC-005-01..07、AC-009-01..06、AC-010-01..06。

## Task 3：环境 doctor、Git/gh 安装策略与身份

**产物：**

- `scripts/auto_git/doctor.py`
- `scripts/auto_git/install.py`
- `scripts/auto_git/identity.py`
- `tests/unit/test_doctor.py`
- `tests/unit/test_install.py`
- `tests/integration/test_identity.py`

**步骤：**

1. 写 OS/Python/PATH/Git/gh/auth/identity capability 与安装计划测试。
2. 观察 RED 后实现只读 doctor、平台包管理器建议和安装后验证。
3. 对 identity local/global 来源、缺失阻断和最小字段计划做临时仓库测试。
4. 确认核心不接收 Token，不自动执行 root/admin 安装。

**覆盖：** US-014、US-015、US-017、US-024；AC-014-01..06、AC-015-01..06、
AC-017-01..06、AC-024-01..06。

## Task 4：仓库事实、fingerprint 与不可变计划

**产物：**

- `scripts/auto_git/git_facts.py`
- `scripts/auto_git/planner.py`
- `tests/unit/test_porcelain_v2.py`
- `tests/integration/test_inspect_and_plan.py`

**步骤：**

1. 用含空格、换行、重命名、未跟踪文件的 fixture 写 porcelain v2/NUL 解析测试。
2. 写非仓库、detached HEAD、merge/rebase、脏状态和 plan 漂移测试并观察 RED。
3. 实现 facts、fingerprint、风险策略和 immutable plan。
4. 验证 plan 修改或仓库变化会导致 hash/fingerprint 拒绝。

**覆盖：** US-001..005；AC-001-01..06、AC-002-01..06、AC-003-01..06、
AC-004-01..06、AC-005-01..07。

## Task 5：精确 staging、回归门禁、Commit 与恢复

**产物：**

- `scripts/auto_git/regression.py`
- `scripts/auto_git/executor.py`
- `scripts/auto_git/recovery.py`
- `tests/integration/test_exact_stage.py`
- `tests/integration/test_regression.py`
- `tests/integration/test_commit_recovery.py`

**步骤：**

1. 先写拒绝空批准、路径漂移、`git add -A/.`、失败/超时/缺命令回归测试。
2. 观察 RED 后实现 NUL-safe `--pathspec-from-file` 精确 staging。
3. 实现可信回归档位、index 备份、Commit postflight 和 operation record。
4. 实现 restore-index/soft-uncommit 的所有权与漂移保护；永不删除工作区文件。

**覆盖：** US-006..010、US-012；AC-006-01..07、AC-007-01..06、
AC-008-01..07、AC-009-01..06、AC-010-01..06、AC-012-01..06。

## Task 6：Remote、Push 与 GitHub adapter

**产物：**

- `scripts/auto_git/remote.py`
- `scripts/auto_git/github.py`
- `tests/integration/test_remote_push.py`
- `tests/integration/test_github_adapter.py`

**步骤：**

1. 用本地 bare remote 和 fake gh 写 create/connect/fetch/ahead-behind/push 测试。
2. 覆盖 visibility 缺失、remote URL 不一致、behind/diverged、non-fast-forward RED。
3. 实现创建仓库不顺带 Push、标准 Remote 独立连接、分支 Push postflight。
4. 扫描并证明没有 force push、凭证参数或 shell 拼接执行路径。

**覆盖：** US-017..020；AC-017-01..06、AC-018-01..07、AC-019-01..07、
AC-020-01..07。

## Task 7：Release readiness、分阶段发布与 resume

**产物：**

- `scripts/auto_git/release.py`
- `tests/integration/test_release.py`
- `tests/integration/test_release_resume.py`

**步骤：**

1. 写版本/CHANGELOG/full regression/build/tag/assets readiness 失败测试。
2. 写 Release Commit、annotated Tag、branch Push、Tag Push、GitHub Release
   五阶段独立审批与 checkpoint 测试并观察 RED。
3. 实现 GitHub Release `--verify-tag`，禁止隐式建 Tag。
4. 模拟中断并验证 resume 幂等；公开资源冲突时停止，不覆盖或删除。

**覆盖：** US-021..023；AC-021-01..07、AC-022-01..08、AC-023-01..07。

## Task 8：统一 CLI、Skill 委托与端到端场景

**产物：**

- `scripts/auto_git.py`
- `scripts/auto_git/cli.py`
- `tests/e2e/test_zero_to_release.py`
- `tests/e2e/test_bootstrap_and_lifecycle.py`

**步骤：**

1. 先写 `doctor/inspect/plan/apply/verify/recover/resume` JSON CLI 合同测试。
2. 实现薄 CLI，不把业务逻辑堆在入口。
3. 用临时仓库、本地 bare remote、fake gh 完成零到 Release E2E。
4. 验证 Skill archive manifest/SHA-256、发现/升级/卸载只做隔离目录模拟。

**覆盖：** US-013..016、US-021..023；对应全部 AC。

## Task 9：Native Plan、全量验证与收尾

**步骤：**

1. 对隔离 candidate 运行 content gate、creation review。
2. 使用 `brief-auto-git-v0-1-0` 生成 Native Plan preview，确认目标为当前项目根。
3. Apply 同一 candidate/plan 后运行 Native Plan verify 与 Skill self-test。
4. Fresh run：pytest、ruff、compileall、危险命令/凭证/占位符/链接扫描、临时 E2E。
5. 更新测试证据、CHANGELOG、README、Architecture、Roadmap、Task、Sprint、daily log、
   Handoff 和 OB Task。
6. 保持 Auto Git 自身未 Commit、未 Push、未创建远程、未 Tag/Release、未 Global 安装；
   把这些后续动作作为独立审批点报告。

**完成门禁：** 所有本地检查为 fresh PASS；若独立 Agent 行为评审因宿主限制未执行，必须
明确标记证据等级，不得把确定性 fixture 冒充独立 LLM 评测。
