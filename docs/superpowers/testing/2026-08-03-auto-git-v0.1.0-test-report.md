# Auto Git 0.1.0 本地测试报告

日期：2026-08-03

状态：Local release candidate verified；真实发布与跨宿主安装待独立审批

## 候选身份

- Authoring Brief：`brief-auto-git-v0-1-0`
- Native Plan：`native-20260803035534-9912211b`
- 初始 Native Plan candidate fingerprint：
  `c94d0611e8b4c8dc5bd4e7ea4c2156a97c9a8a90b5f6d7664662f030f47a5fc0`
- 最终 38 文件 Native Plan candidate fingerprint：
  `73f6bb5fbb85458e27e2cb4fd957290adfe1339336cc241b2745043b51f07b60`
- 最终 Native Plan：
  `.skill-engineering/native-plan-auto-git-v0.1.0-final-review.json`
- 文件数：37
- production creation review：100/A

标准安装、双语文档和双远程校验属于该基线后的已验收修订。精确候选已同步并重新通过
content gate、production review 与 self-test；真实发布前仍需生成与当时源状态绑定的
最终 Native Plan，不沿用旧 fingerprint。

## TDD 证据

1. 初始测试因 `auto_git` 包不存在产生 5 个 collection RED。
2. 第一轮最小实现后 18/19；唯一失败证明 release readiness 正确阻断脏工作区，修正
   测试夹具后 19/19。
3. 统一 CLI 与 Release resume 先因缺少 `release_status` 产生 RED，实现后 21/21。
4. 回归副作用漂移、GitHub auth、Skill 生命周期和归档 manifest 先因 API 缺失产生
   RED，实现后 24/24。
5. 双语 README、用户 Playbook、标准 Skill 安装和 OB/布丁同源契约先产生 17 个失败、
   1 个跳过；文档落地后 19/19。
6. 双远程 branch/annotated Tag 一致性先因 `verify_mirror_refs` 不存在产生 RED；实现
   本地 bare remote 校验后转 GREEN。CLI `verify-mirrors` 再先因子命令不存在产生
   RED，实现后目标 CLI/Remote 测试 14/14。
7. Release reference 的双远程 postflight 先因缺少命令和一致性说明产生 RED，补齐
   `verify-mirrors` 契约后转 GREEN。
8. 首装自举契约先因 README/Skill 仍暗示“先装 Auto Git、再检查 Git”进入 RED；
   复核标准 Skills CLI 官方 `add.ts/git.ts` 后，固定“宿主先准备 Git → 标准安装
   Auto Git”，并同步中英 README、Playbook、Reference、Spec/ADR 与布丁草稿后转 GREEN。
9. 独立代码审查发现恢复可绕过计划、Remote 参数注入、fetch 失败被忽略、首次 Push
   无 upstream、CLI/Spec 漂移和过宽 Claude allowlist；先扩充 failure/high-risk
   测试产生 RED，再完成 fail-closed 恢复、Remote 校验、稳定 CLI 错误合同和权限收窄。
10. 第二轮独立审查继续发现 Remote URL 凭证持久化、Release identity/readiness/
    postflight、record 假验证、GitHub account 与原子恢复缺口；逐项增加 RED fixture，
    完成 URL sanitize、profile 驱动 Release、逐 action verifier、GitHub 回读、原子
    index 替换和动作级 plan schema 后转 GREEN。

## Fresh 验证

| 检查 | 结果 |
|---|---|
| `AUTO_GIT_PUDDING_MANUAL=... PYTHONPATH=scripts python3 -m pytest -q` | 114 passed |
| 最终 Native Plan 隔离目标 `pytest -q tests` | 91 passed |
| `ruff check --no-cache scripts tests` | pass |
| `python3 -m compileall -q scripts .claude/hooks` | pass |
| `.claude/settings.json` JSON 解析 | pass |
| 活跃 `.claude` 运行占位符扫描（排除 `.new`） | 0 finding |
| Skill Engineering content gate（修订后精确候选） | pass，0 finding |
| production creation review | 100/A |
| Skill self-test | content/review/declared test/compile 全 pass |
| 危险执行路径扫描 | 未发现 force、破坏性 reset/clean、shell=True 或宽泛 staging |
| candidate → 保存项目 dry-run compare | 文件内容一致，仅时间戳不同 |
| doctor | Python/Git/gh 可用；Git identity 完整；gh auth=false |
| inspect 当前项目 | 正确识别 `main`、initial HEAD、大量未跟踪初始文件 |
| OB Task 严格 schema | 0 error / 0 warning |

根项目包含 ANK harness、docs 和模板说明，因此不能把整个工程根当成纯 Skill 发布包
运行 content gate；发布门禁以 Native Plan 绑定的 38 文件精确 candidate 为准。
第一次 37 文件隔离包全测得到 82 passed / 1 failed，暴露 `.auto-git.toml` 未进入候选；
补入该无凭证 Release profile 后重新生成 Plan，apply/verify 与 83 项测试全部通过。

## 覆盖场景

- canonical JSON/hash、plan 篡改和 fingerprint 漂移；
- porcelain v2/NUL、空格路径、非仓库和 initial HEAD；
- argv-only runner、超时/缺命令边界、原子 JSON 和仓库锁；
- identity 阻断、精确 staging、回归失败和回归副作用二次漂移；
- index 备份所有权与 checksum 恢复；
- 恢复独立 plan/approval、受管 record 路径、备份/current-index checksum 与 undo backup；
- local bare Remote 连接、fetch fail-closed、参数注入阻断、首次 upstream、Push postflight、
  URL 冲突；
- GitHub visibility 阻断、fake `gh`、Release `--verify-tag`；
- GitHub `owner/repo`、Tag 名称的选项注入/路径穿越/无效 ref 阻断；
- Remote URL user-info/query/fragment/credential 拒绝与脱敏 identity record；
- `.auto-git.toml` Release profile、branch/upstream/Tag/assets readiness 失败矩阵；
- GitHub account/protocol、repo create 和 Release 的结构化 postflight；
- 各写入 action 独立 record verifier，未知 action 明确 unknown；
- index 同目录临时写、fsync、checksum、原子 replace 与失败保全；
- action 参数 schema、plan summary/risk/postconditions/rollback 和无时间过期策略；
- release readiness、Tag checkpoint/resume；
- GitHub hostname/repository 显式绑定，`GH_HOST/GH_REPO` 环境重定向失效；
- operation record 幂等重放、postcondition 漂移拒绝、锁内二次校验；
- fingerprint 覆盖工作区内容、index、本地配置/Remote 和操作状态；
- 锁记录 pid/action/repo/started_at，并对 stale lock 给出人工恢复诊断；
- Release resume 读取明确仓库的现有 Release，完全一致完成、冲突 fail closed；
- GitHub Provider annotated Tag object/target 与本地和配置 Remote OID 三方一致；
- Release asset 同时核对名称与 GitHub 服务端 `sha256:` digest；
- plan 不设置时间过期，幂等重放只由 record 身份和当前 postcondition 决定；
- fingerprint 覆盖 effective Git config 和改动路径 mode；
- 非 Git 目录 fingerprint 递归覆盖相对路径、类型、mode、size、mtime 与 symlink target；
- 畸形 operation record 在 Provider I/O 前 fail closed，verifier 不外泄异常；
- 顶层 record/repo/action/details 类型异常统一返回结构化 drifted，CLI 无 traceback；
- GitHub/Gitee 本地 bare remote branch OID、annotated Tag target 一致和缺失 ref 阻断；
- `verify-mirrors` CLI 的双远程只读 postflight；
- CLI dependency/auth/release/history、受管 recovery，以及稳定 JSON/human 错误输出；
- Claude permissions 不自动放行 Git 写入、通用 Python/Node/curl；
- Skill archive manifest/SHA-256、project/profile/global 生命周期预览；
- 中文/英文 README 互链与关键事实、中文用户 Playbook、标准 `npx skills` 安装契约；
- 仓库用户手册与 OB 布丁发布副本去 frontmatter 后正文一致；
- success、failure、high-risk、holdout 行为案例。

## 布丁同步 postflight

- 发布副本：
  `/Users/aim5/Documents/OB/_OB工程/publications/auto-git/Auto Git 用户手册.md`
- Case ID：`cmscwjpjp00e5pokaitm2t42c`
- 状态：`draft`
- 后台：
  `https://aixiaoai.cloud/admin/cases/cmscwjpjp00e5pokaitm2t42c/edit`
- 首次 apply：1 新建、0 更新、0 跳过、0 失败。
- 首装自举说明修正后 apply：0 新建、1 更新、0 跳过、0 失败。
- 发布候选安装可用时点提示修正后 apply：0 新建、1 更新、0 跳过、0 失败。
- `pudding status` 能识别该 Case 已同步；CLI 同时提示本地 mtime 晚于
  `pudding_synced`。正文同源测试通过，因此未为纯 mtime 提示盲目重复 apply。

当前只可声明“布丁草稿已同步”，不能声明“已公开发布”；draft 没有公开 URL。

## 宿主真实样本

当前宿主 Agent 在 `/private/tmp/auto-git-host-trial-20260803` 执行：

1. inspect 识别 `main`、initial HEAD 和唯一未跟踪 `README.md`；
2. plan 固定精确路径和 hash；
3. plan 首次写入目标仓库后触发 fingerprint 漂移，未执行；
4. 将 plan 移到仓库外状态路径后，使用同一 hash 完成精确 Commit；
5. record verify 返回 `verified: true`。

这证明一个真实本地任务可用，但不是独立模型、跨宿主或真实 GitHub 用户试用；不能把
它扩张为完整市场效用结论。

## 尚未执行

- Auto Git 自身首次 Commit；
- 真实 GitHub 登录、仓库创建、Push、Tag 和 Release；
- 真实 GitHub/Gitee 源的同 Commit/Tag postflight；
- Git/gh 系统级安装；
- project/profile/global 的真实宿主安装、升级和卸载；
- 独立 Agent/真实用户跨宿主试用。

这些动作不是测试失败，而是明确的权限和发布门禁；分别批准后再补 release record 与
真实远端 postflight。
