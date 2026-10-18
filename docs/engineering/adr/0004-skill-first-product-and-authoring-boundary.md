# ADR 0004：Auto Git 采用 Skill-first 产品形态

状态：Accepted（用户于 2026-08-03 明确确认）

日期：2026-08-03

> 发行方式更新：第 6 条已由 ADR 0005 修正为标准仓库型 Skill 安装、GitHub 主源和
> Gitee 同提交镜像；Skill-first 产品形态及其他条款继续有效。

## 背景

Auto Git 的最终用户通过 Agent 使用自然语言完成 Git 安装引导、仓库初始化、Commit、
Remote、Push、Release 和恢复。此前文档把产品描述为“Agent Skill + 独立 pipx CLI”，
容易让用户需要安装两个产品，也把 Skill Engineering 与 Auto Git 的关系写反。

用户已经确认：

- Auto Git 本身是一个独立 Skill；
- Skill Engineering 是已经存在的另一个 Skill 项目，用来创建、工程化和维护 Auto Git；
- 用户最终安装和使用的是 Auto Git Skill，而不是 Skill Engineering 或单独的 Auto Git CLI。

## 候选方案

### A. Skill-first，确定性核心随 Skill 分发

- 仓库根以 `SKILL.md` 作为产品入口；
- `skill.contract.yaml` 固定输入、输出、停止点、审批、副作用和测试；
- Git 状态、计划、执行、验证和恢复代码放在 Skill 自身的 `scripts/`；
- 用户只安装 Auto Git Skill；
- Skill Engineering 只在开发期创建和治理，不进入运行时。

优点：产品心智和安装对象唯一；符合 Agent Skill 的自然语言编排能力；确定性逻辑仍可
独立测试。代价：必须验证 Skill 安装、脚本运行时和不同 Agent 宿主的兼容性。

### B. Skill 编排独立 pipx CLI

- 用户先安装 Auto Git Skill；
- 还需额外安装 `auto-git` Python CLI；
- Skill 通过版本化 JSON 调用外部 CLI。

优点：CLI 可脱离 Agent 单独使用。缺点：双重安装、版本配对和 PATH 漂移明显增加新手
负担；“Auto Git 是一个 Skill”的产品边界不再清晰。

### C. Auto Git MCP Server

- 通过长期运行的 MCP Server 暴露 Git 工具；
- Skill 或 Agent 通过 MCP 调用。

优点：适合多个客户端共享服务、集中策略或远程执行。缺点：需要额外服务进程、配置、
认证和生命周期管理；`0.1.0` 的本地 Git 工作流不需要这些能力。

## 决策

选择方案 A。

1. Auto Git 是一个复杂、生产级、具有外部副作用的 Agent Skill。
2. Auto Git 独立仓库的可交付根结构为：

   ```text
   SKILL.md
   skill.contract.yaml
   agents/
   scripts/
   references/
   tests/skills/auto-git/cases/
   docs/
   ```

   没有真实内容的可选目录不创建。
3. 根 `SKILL.md` 只承担触发、反触发、路由、输入输出、停止点、审批和反馈，不堆积
   Git 状态机实现。
4. 确定性的环境探测、Git 事实读取、不可变计划、执行、验证、记录和恢复逻辑全部位于
   `scripts/`，并通过版本化 JSON 契约供根 Skill 调用。
5. 用户安装对象只有 Auto Git Skill。`0.1.0` 不要求用户再安装独立 pipx CLI。
6. `0.1.0` 的无 Git 首次获取路径固定为 Auto Git GitHub Release Skill 归档：
   归档包含完整 Skill manifest 和 SHA-256 清单，由 Agent/用户通过浏览器或宿主下载
   能力取得，再按已预览的目标宿主与范围安装。Git 可用后可以迁移到基于仓库的标准
   Skill 安装路径。具体宿主命令必须在真实干净环境验证后固定，不在 ADR 中猜测。
7. Skill Engineering 是开发期治理和 Native Authoring 工具，负责 Authoring Brief、
   独立候选、预览、门禁、评测、安装审计和版本维护；Auto Git 运行时不依赖它。
8. Superpowers/TDD 可以由开发流程内部调用，但不与 Skill Engineering 并列成为第二套
   顶层治理流程。
9. MCP、长期服务、独立 pipx CLI 和单文件二进制均不进入 `0.1.0`；只有出现明确的
   多客户端共享、后台服务或脱离 Agent 使用需求后再单独 ADR。

## Skill 与 Scripts 边界

### Skill 负责

- 理解用户的自然语言意图和反馈层级；
- 确认目标项目、任务文件范围和必要业务输入；
- 调用只读脚本获取事实；
- 解释计划、风险、审批、结果和恢复；
- 在每一种写入或公开动作前取得对应用户批准。

### Scripts 负责

- 只从操作系统、Git、GitHub CLI 和版本化配置读取机器事实；
- 生成不可变计划、fingerprint、记录和 checkpoint；
- 使用参数数组执行已批准动作，不拼接自由 shell；
- 实施漂移、并发、精确 staging、远端和恢复门禁；
- 输出稳定 JSON，且不保存凭证或完整敏感 diff。

### 禁止跨界

- Skill 不绕过 scripts 直接执行写入型 Git；
- scripts 不解释模糊自然语言，也不自行假设用户已经批准；
- Skill Engineering 不作为 Auto Git 的运行时 delegate；
- 0.1.0 不把 MCP 当成安装 Auto Git Skill 的必要条件。

## 后果

### 正向

- 用户只需理解和安装一个产品：Auto Git Skill；
- 产品源码、确定性执行代码、契约和测试可以在同一仓库独立开源；
- Skill Engineering 能完整治理 Auto Git，又不会成为用户运行时依赖；
- 未来仍可从稳定 JSON 契约派生独立 CLI 或 MCP Adapter。

### 代价

- 需要验证不同 Agent 宿主如何定位和运行 Skill 内脚本；
- 无 Git 环境下的 Skill 首次获取必须有专门的 bootstrap 验收；
- Python 运行时是否适合作为 Skill 内脚本依赖需要在 ADR 0002 与真实兼容测试中确认；
- 原 PRD/Spec 中 pipx 自安装、`auto-git` 全局命令和 Skill Engineering 后置集成表述
  必须同步修正。

## 被本 ADR 修正的旧决策

- ADR 0001 的“确定性独立 CLI + Agent Skill”产品形态，改为“Skill-first + bundled
  scripts”；独立产品和独立仓库决策继续有效。
- ADR 0001 中“只做 Skill：拒绝”不再有效。
- ADR 0003 中 pipx 作为 Auto Git 用户安装基线的条款不再有效；零到 Release 范围和
  GitHub-first 决策继续有效。
- ADR 0002 继续评估 Python，但定位改为 Skill 内 `scripts/` 的确定性实现，而不是
  用户单独安装的产品 CLI。
