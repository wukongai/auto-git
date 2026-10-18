# Auto Git 0.1.0 标准发行与用户文档 TDD Plan

状态：Local execution complete（真实 GitHub/Gitee 发布与跨宿主安装待独立审批）

执行结果：文档与 Reference 契约均按 RED → GREEN 落地；独立审查整改后 fresh 全量
测试 114 passed，最终 38 文件纯 Skill 候选测试 91 passed，
ruff/compileall 通过；修订候选通过 Skill Engineering content gate、production review
100/A 和 self-test；布丁 draft Case `cmscwjpjp00e5pokaitm2t42c` 已创建。未执行
Commit、建仓、Push、Tag、Release 或 Global 安装。

关联：

- [Auto Git 0.1.0 PRD](../../PRD.md)
- [Auto Git 0.1.0 Spec](../specs/2026-08-02-auto-git-v0.1.0-spec.md)
- [标准 Skill 双远程发行 Design](../specs/2026-08-03-auto-git-standard-skill-dual-remote-distribution-design.md)
- [ADR 0005](../../adr/0005-standard-skill-dual-remote-distribution.md)

## 目标

在不创建自定义安装器、不提前执行 Git 公开动作的前提下，交付：

1. GitHub/Gitee 标准 Skill 双源安装说明；
2. 中文 `README.md` 与英文 `README.en.md`，顶部互相切换；
3. 独立中文用户手册，作为比 README 更具体的操作 Playbook；
4. 与仓库正文同源、仅在 OB 保存布丁元数据的发布副本；
5. 布丁 dry-run、apply 和 status postflight；
6. 双远程发行的本地验证契约和真实发布前审批清单。

## 技术与安全边界

- 文档测试使用 Python 标准库与 pytest，不新增运行时依赖；
- 标准安装命令使用 `npx skills`，不创建 `install.sh` / `install.ps1`；
- 仓库不保存 `pudding_id`、布丁后台 URL、同步时间或凭证；
- OB 发布副本可以保存布丁 CLI 真实回填的同步元数据；
- 本计划授权本地文档、测试、OB 发布副本和用户已明确要求的布丁同步；
- 本计划不授权 Git Commit、创建 GitHub/Gitee 仓库、Push、Tag、Release 或 Global
  Skill 安装，这些动作继续使用独立事实预览和审批。

## 验收追踪

| Requirement | Plan Task |
|---|---|
| US-016-AC07/08 | Task 2、Task 6 |
| US-025-AC01/02 | Task 1、Task 2 |
| US-025-AC03/04/05/06 | Task 1、Task 3 |
| US-025-AC07/09 | Task 1、Task 4 |
| US-025-AC08 | Task 5 |

## Task 1：建立文档契约测试（RED）

**创建：**

- `tests/unit/test_user_documentation.py`

**验证对象：**

- `README.md`
- `README.en.md`
- `docs/tutorials/auto-git-user-manual.zh-CN.md`
- OB `_OB工程/publications/auto-git/Auto Git 用户手册.md`

**步骤：**

1. 写测试要求中英 README 文件存在，且首屏包含双向语言切换链接；
2. 写测试要求两版包含同一版本、GitHub/Gitee 安装、project/global、Codex/Claude Code、
   更新、卸载、用户手册、安全审批和“不是后台自动提交”边界；
3. 写测试要求中文用户手册包含安装、doctor、Git identity、init/inspect、Commit、
   Remote、首次/后续 Push、Release、恢复、更新和卸载章节；
4. 写测试要求手册包含可复制自然语言示例、预期结果和故障处理；
5. 写测试禁止公开仓库出现 `pudding_id`、布丁后台 URL 和同步时间；
6. 写测试对仓库手册与 OB 副本去除 YAML frontmatter 后做正文一致性比较；
7. 运行 `python3 -m pytest -q tests/unit/test_user_documentation.py`，确认因目标文件缺失或
   内容不足进入 RED；不得先创建生产文档再补测试。

## Task 2：重写中英 README（GREEN）

**修改：**

- `README.md`

**创建：**

- `README.en.md`

**中文与英文共同结构：**

1. 语言切换；
2. 一句话产品价值；
3. 适合谁、能完成什么；
4. 安装前提和 GitHub/Gitee 标准安装；
5. 第一次对 Agent 说什么；
6. 日常 Commit/Push/Release 示例；
7. 审批、凭证和恢复边界；
8. 支持宿主与已验证范围；
9. 用户手册、问题反馈和开发者文档入口。

**步骤：**

1. 中文版以普通用户结果为主，不把 Native Authoring、TDD 或内部测试放在首屏；
2. 英文版不是逐字机器翻译，保持相同事实、命令、边界和链接；
3. 所有命令逐条解释用途、参数和影响；
4. 运行文档测试，先让 README 相关断言转 GREEN；
5. 人工对照两版标题层级和链接，记录无法自动判断的语义差异。

## Task 3：编写中文用户手册 Playbook（GREEN）

**创建：**

- `docs/tutorials/auto-git-user-manual.zh-CN.md`

**章节：**

1. Auto Git 是什么、不会做什么；
2. 准备一个支持 Skill 的 Agent；
3. 从 GitHub/Gitee 安装；
4. 第一次运行 doctor；
5. 没有 Git/Python/gh 时怎么办；
6. 配置 Git 姓名和邮箱；
7. 新文件夹初始化与已有项目检查；
8. 准备和确认 Commit；
9. 连接/创建 GitHub 或 Gitee Remote；
10. 首次 Push 与后续 Push；
11. Tag 与 GitHub Release；
12. 失败、漂移和恢复；
13. 更新与卸载；
14. 常见问题、成功检查和获取帮助。

**步骤：**

1. 每章先给一条用户可复制给 Agent 的自然语言；
2. 接着说明 Auto Git 会检查什么、为什么停下、何时需要用户确认；
3. 给出预期结果和至少一个常见错误恢复入口；
4. 不要求用户阅读 PRD/ADR/源码，不把训练营作为产品功能；
5. 运行文档测试，让用户手册断言转 GREEN。

## Task 4：创建 OB 布丁发布副本与同源检查（GREEN）

**创建：**

- `/Users/aim5/Documents/OB/_OB工程/publications/auto-git/Auto Git 用户手册.md`

**允许的发布 frontmatter：**

- `title`
- `description`
- `type: text`
- `source`
- `published`

首次创建不得编造：

- `pudding_id`
- `pudding_url`
- `pudding_public_url`
- `pudding_synced`

这些字段只能由布丁工具在 apply/postflight 中真实产生。

**步骤：**

1. 用仓库中文手册正文创建 OB 发布副本；
2. source 暂使用已确认的公开 GitHub 仓库 URL；远程尚未创建前保留显式发布占位状态，
   不编造 URL；
3. 运行正文同源测试；
4. 确认仓库文件无布丁元数据，OB 副本 frontmatter 不包含凭证。

## Task 5：布丁 dry-run、apply 与 postflight

**目标：**

- OB 发布副本

**步骤：**

1. 运行 `pudding sync "<OB user manual>" --verbose`，保持默认 dry-run；
2. 检查环境为 prod、动作类型、标题、description、正文长度、链接和媒体；
3. dry-run 无 error 且内容与已确认手册一致后，执行相同目标加 `--apply`；
4. 运行 `pudding status "<OB user manual>"`；
5. 读取 CLI 回填的 `pudding_id`、后台 URL、状态和 `pudding_synced`，不得手写；
6. draft 状态验证后台 Case 已创建；只有 published 状态才要求打开并验证公开 URL；
7. 把 Case 状态、真实 URL 与验证摘要写入测试报告、Task、Daily Log 和 OB Task；
8. 若 apply 失败，保留 OB 副本和 dry-run 证据，标记 waiting-sync，不声称已发布。

## Task 6：标准安装与双远程发行本地契约

**修改：**

- `references/install.md`
- `SKILL.md`（仅当现有触发/反馈缺少标准安装边界）
- `docs/superpowers/testing/2026-08-03-auto-git-v0.1.0-test-report.md`

**测试：**

- 扩展 `tests/unit/test_user_documentation.py`
- 必要时扩展现有 install/remote integration tests

**步骤：**

1. 先写旧 Release ZIP 基线应失败、GitHub/Gitee 标准源应出现的断言；
2. 将运行时安装参考改为标准 Skills CLI，删除旧归档首装契约；
3. 验证 GitHub/Gitee source、版本和关键文件 hash 一致性所需本地逻辑/检查；
4. 使用本地 bare remote/fake URL 验证双 remote branch OID 与 Tag target 比较；
5. 不接触真实 GitHub/Gitee，不读取 Token，不执行 Push；
6. 全部本地测试通过后才进入真实发布审批。

## Task 7：Fresh 全量验证与文档对齐

**命令：**

```bash
python3 -m pytest -q
ruff check --no-cache scripts tests
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q scripts
```

**补充检查：**

1. 中英 README 链接与关键事实；
2. 仓库/OB 手册正文同源；
3. 仓库没有布丁元数据、凭证和后台 URL；
4. `pudding status` 显示已同步，或明确记录 waiting-sync；
5. 更新 Product、PRD、Spec、Architecture、Roadmap、Task、Sprint、Daily Log、Handoff、
   CHANGELOG、测试报告和 OB Task；
6. 保持 Git 未 Commit、无 remote、无 Push、无 Tag/Release，等待独立发布审批。

## 完成门禁

- 文档契约测试先 RED 后 GREEN；
- 全量 pytest、ruff、compileall fresh PASS；
- Skill Engineering 内容门禁与 production review fresh PASS；
- 中文/英文 README 关键事实一致；
- 用户手册覆盖 US-025-AC03..06；
- OB 副本正文与仓库同源；
- 布丁真实 Case 状态经过 postflight；只有 published 才声明和验证公开 URL；
- 未越权执行 Git Commit、远程创建、Push、Tag、Release 或 Global 安装。
