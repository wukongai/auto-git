# ADR 0003：0.1.0 采用零到 Release 纵向闭环与 GitHub 首适配器

状态：Accepted（安装形态条款由 ADR 0004 修正）

日期：2026-08-03

> 2026-08-03 更新：零到 Release 和 GitHub-first 决策继续有效；Auto Git 的用户安装
> 对象已由 ADR 0004 改为 Auto Git Skill，不再以独立 pipx CLI 为基线。

## 背景

原 `0.1.0` 只覆盖本地 inspect、workspace、Commit、verify 和 recovery，把安装、Remote、
Push、Tag 与 Release 延后到 `0.2.0`。用户指出真正的 Git 新手可能连 Git 都不会安装，
如果产品不能从环境准备走到远端发布，就仍需要用户在最困难的边界自行拼接流程。

同时，首版若一次覆盖 GitHub、GitLab、Gitee 的账号、仓库创建、认证和 Release API，
会让 Provider 差异淹没 Git 确定性核心。

## 候选方案

### A. 0.1.0 端到端纵向闭环，GitHub 首适配器

- 覆盖 Auto Git/Git/GitHub CLI 安装、init、Commit、Remote、Push、Tag、GitHub Release；
- 标准 Git Remote 和 Push 保持 Provider-neutral；
- GitHub 是首个专用认证、仓库创建和 Release Adapter；
- 高风险动作保持独立 plan、审批、record 和 postflight。

优点：首版用户能完成真实“从零到发布”结果；Core 不绑死 GitHub。缺点：0.1.0 范围
扩大，必须按纵向里程碑拆 TDD Plan。

### B. 产品 PRD 完整，但 0.1.0 仍只做本地

优点：实现范围最小。缺点：第一版无法解决用户明确提出的安装、远端和发布问题，
产品价值仍在本地 Commit 处中断。

### C. 0.1.0 同时完整覆盖多个 Provider

优点：平台覆盖广。缺点：认证、权限和 Release 差异使首版范围不可控，也增加凭证和
兼容风险。

## 决策

选择方案 A。

`0.1.0` 必须提供一个可验证的零到 Release 纵向场景：

```text
安装 Auto Git Skill
→ doctor
→ 安装/验证 Git 与 GitHub CLI
→ init / Commit
→ 创建或连接 Remote
→ Push
→ Release readiness
→ Release Commit
→ annotated Tag
→ Push branch
→ Push single Tag
→ GitHub Release
→ verify / resume
```

边界如下：

1. Auto Git 以 Skill 形式安装；`0.1.0` 至少验证一条不要求用户预装 Git 的获取路径，
   不再要求用户额外安装 pipx CLI。
2. 标准 Remote、fetch、ahead/behind 和 Push 属于 Core，不绑定 Provider。
3. GitHub CLI 是 `0.1.0` 首个 Provider Adapter，负责 auth status、repo create 和
   Release。
4. 创建 GitHub 仓库不得顺带 Push。
5. Release 必须引用已经在远端验证存在的 annotated Tag，不允许 Provider 隐式建 Tag。
6. Commit、remote create/connect、Push、Tag、Tag Push、Release 分别审批。
7. 0.1.0 不执行 PR、merge、force push、自动冲突解决或包注册表发布。
8. GitLab/Gitee 可连接标准 Git Remote 并 Push；专用仓库创建和 Release API 延后。

## 后果

### 正向

- 普通用户不需要先自行安装和理解 Git 才能进入产品；
- 0.1.0 能交付可感知的完整成果，而非半段工作流；
- Provider-neutral Core 仍可被 GitLab、Gitee 和自托管 Git 复用；
- 公开动作有独立 postflight 和断点恢复，不依赖 Agent 聊天记忆。

### 代价

- PRD 从 13 个扩展到 24 个 User Stories；
- 测试矩阵新增 OS 安装、PATH、认证、Remote、网络不确定性和部分 Release；
- TDD Plan 必须拆成环境安装、本地核心、Remote/Push、Release、恢复/自举多个里程碑；
- Skill 获取、宿主发现和 Python scripts 运行时需要分别验证，尤其是无 Git 环境。

### 后续复评

- Skill 获取或 Python scripts 运行时是否成为主要采用障碍；
- 是否需要签名单文件二进制或原生安装器；
- GitLab/Gitee 哪一个成为第二个 Provider Adapter；
- 包注册表发布是否进入独立产品能力和 ADR。
