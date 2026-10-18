# ADR 0002：Skill 内 Python Scripts 与版本化 JSON 契约

状态：Accepted

日期：2026-08-02

## 背景

Auto Git Skill 的确定性 scripts 需要安全启动 Git 子进程、解析 NUL 分隔机器输出、
保存版本化 plan/record schema、检测漂移、实现跨平台锁和恢复，并提供根 `SKILL.md`
可稳定调用的脚本入口。

本机有 Python 与 Node.js，但 ANK 检测到多个 Node 来源且项目未钉 Node 版本；Rust
工具链未安装。相邻的 agent-skill-hub 与 Skill Engineering 已验证 Python 中的
plan hash、fingerprint、atomic record 和 safe undo 模式，但 Auto Git 不得依赖或
复制它们的业务实现。

## 决定

1. `0.1.0` 确定性核心使用 Python 3.11+，源码随 Auto Git Skill 放在 `scripts/`。
2. 运行时依赖以标准库为限：
   - `subprocess` 只传 program + argv，默认 `shell=False`；
   - `dataclasses`、`json`、`hashlib` 定义 schema 和 canonical hash；
   - `tomllib` 只读项目配置；
   - 原子文件和锁通过标准库实现。
3. `scripts/` 的入口同时支持人类文本和版本化 JSON；根 Skill 只依赖 JSON 契约。
4. 核心与 ANK、Skill Engineering、Agent runtime、Provider 保持单向隔离。
5. 开发依赖可以包含 pytest、ruff 和 Python 构建后端，但不能渗入运行时协议。
6. 开发项目声明 Python 版本并使用独立虚拟环境；用户运行时由 Skill doctor 检测
   Python capability，不依赖 notebooklm 等私有环境。
7. 纯 shell 只用于可选 hook dispatcher，不承载核心状态机。

## 结果

### 正面

- 最低首版成本，能快速建立可测试的 inspect/plan/apply/verify/recover 闭环；
- 参数数组调用 Git，避免把路径和用户输入交给 shell；
- JSON、hash、临时仓库测试和相邻工程经验可直接用于设计验证；
- 根 `SKILL.md` 可通过稳定 JSON scripts 契约调用确定性核心。

### 负面

- 目标 Agent 宿主需要合适的 Python，缺失时 Auto Git 只能先提供安装引导；
- `0.1.0` 不把确定性核心作为独立 pipx 产品分发；若 Python 成为真实采用障碍，再
  单独评估 Node、签名单二进制或宿主原生运行时；
- 标准库优先会增加少量脚本入口、schema 校验和跨平台 state-dir 代码。

### 中性

- 本决定不承诺永远使用 Python；
- 只有真实安装、启动或性能证据证明 Python 成为瓶颈时，才新增 ADR 评估 Rust。

## 替代方案

### Node.js

拒绝作为 `0.1.0` 首选。`spawn/execFile` 可以安全调用 Git，JSON 也自然，但本机已出现
Node 多来源漂移；单文件分发仍处于活跃演进，不能消除首版运行时问题。

### Rust

延后。单二进制、类型安全和 `std::process::Command` 很适合长期核心，但当前没有
工具链，开发和打包矩阵会显著拉长首个可信闭环。

### 纯 shell

拒绝。它适合薄 hook，不适合 NUL-safe parser、版本化 schema、原子记录、跨平台锁、
幂等和恢复状态机。

## 确认记录

用户于 2026-08-03 以 Go 模式确认 `0.1.0` Skill-first Spec，并授权本地开发和完整
验证。本 ADR 同步转为 Accepted；公开 Git 动作和 Global 安装仍保留独立审批。
