---
name: auto-git
description: Use when 用户希望通过自然语言检查、安装或初始化 Git，安全完成精确 Commit、连接或创建远程仓库、Push、Tag、GitHub Release，或恢复 Auto Git 上一次操作；也适用于“不懂 Git 命令、先给计划再执行”的真实项目。不要用于只解释 Git 概念、PR/merge/force push、自动解决冲突、包注册表发布、保存凭证，或修改/发布 Auto Git Skill 自身。
---

# Auto Git

把用户当作不需要记 Git 命令的项目负责人。先说结论、风险和下一步，再用机器事实和
确定性脚本工作。每条展示给用户的命令都解释用途、关键参数和实际影响。

## 输入与输出

输入是用户明确指定的项目路径（缺失时可用当前目录，但必须回显）、目标动作，以及
必要的提交范围、Remote、版本和发布资料。不得接收 Token、私钥、Cookie 或密码。

输出包括中文解释，以及 `schema_version=1` 的 facts、immutable plan、operation
record 和 verification record。只有 postflight 与目标事实一致时才报告成功。

## 固定工作流

1. 运行 `scripts/auto_git.py doctor --repo <path> --json`，检查 Python、Git、gh 和
   identity；缺能力时读取 [安装策略](references/install.md)。
2. 运行 `scripts/auto_git.py inspect --repo <path> --json`，以 porcelain v2/NUL、
   HEAD、分支、操作中状态和 fingerprint 为事实源。
3. 按用户目标生成 immutable plan。先展示文件范围、回归、风险、恢复路径和本阶段
   副作用；用户未确认同一 plan hash 时停止。
4. 每个写入阶段先重新校验 plan hash、fingerprint 和仓库锁，再委托 bundled script。
   Commit、Remote、Push、Tag、Tag Push、GitHub Release 的批准互不继承。
5. 执行 postflight 并保存 record。失败或部分成功时明确已完成阶段、未完成阶段和唯一
   安全下一步；不得用下一阶段掩盖本阶段失败。

详细操作读取 [工作流](references/workflow.md)、[安全边界](references/safety.md)；
发布任务还要读取 [Release](references/release.md)。不要把这些 reference 全量复述
给用户，只加载当前阶段需要的部分。

## 意图路由

- “没有 Git/gh”：已安装的 Auto Git 只生成平台安装策略、审批点和验证命令；
  `0.1.0` 不自动 root/admin 安装。Auto Git 尚未安装且系统没有 Git 时，首次自举由宿主 Agent
  通过系统官方入口先准备并验证 Git，再使用标准 Skills CLI 安装 Auto Git；
  不创建私有安装器或假装未安装的 Skill 可以先运行。
- “初始化/配置身份”：先检查目录、现有 `.git`、local/global 来源；默认 local
  identity，Global 需单独审批。
- “提交”：列出精确路径，运行可信回归，保护 index，再精确 staging、Commit 和
  postflight。永久不使用宽泛 staging。
- “远程/Push”：创建仓库与连接 Remote 分开；先 fetch，再判断 ahead/behind/diverged；
  behind、diverged、non-fast-forward 或 URL 不一致时停止。双远程发行时分别审批
  Push，最后用 `verify-mirrors` 证明 branch OID 与可选 annotated Tag target 一致。
- “Release”：按 readiness → Release Commit → annotated Tag → branch Push →
  单 Tag Push → GitHub Release 分阶段推进和记录 checkpoint。readiness 必须读取项目
  `.auto-git.toml` 的显式 release profile；缺失字段时停止，不从聊天猜发布配置。
- “恢复/继续”：只操作当前 record 拥有且未漂移的备份、Tag 或 checkpoint；公开历史
  只解释和继续，不删除、不覆盖、不改写。

## 停止与禁止条件

- 路径不明确、仓库处于 merge/rebase/cherry-pick、detached HEAD 或事实解析失败。
- 缺 identity、回归失败/超时/命令缺失、计划或仓库漂移、锁冲突。
- Remote 未 fetch、远端领先/分叉、受保护分支、可见性未明确或认证不完整。
- 请求 force push、reset hard、clean、自动 stash、自动冲突解决、绕过测试或保存凭证。
- 请求 PR、merge、包注册表发布，或修改/安装/发布 Auto Git Skill 自身；后者交给
  Skill Engineering 和宿主安装治理。

停止时保留用户文件和已验证记录，不猜测成功，不运行替代性的破坏命令。

## 行为示例

- 用户：“只提交 `README.md`，另一个草稿别动。”预期：plan 只列 `README.md`，回归
  通过后只暂存并提交它，草稿保持未跟踪/未暂存。
- 用户：“直接 force push 覆盖远端。”预期：拒绝执行，报告 fetch 后 ahead/behind
  事实，建议用户人工选择同步或恢复路线。
- 用户：“发布 0.1.0。”预期：先给 readiness 结果；五个写入阶段分别审批，GitHub
  Release 必须验证已存在且已推送的 annotated Tag。
