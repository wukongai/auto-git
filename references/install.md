# 安装与环境策略

## Auto Git 首次获取

Auto Git 使用标准 Agent Skill 安装方式，不要求独立 Auto Git CLI、MCP Server 或
Skill Engineering 运行时。

标准仓库型 Skills CLI 会通过 Git 获取 Auto Git，因此首装需要：

- 一个支持 Agent Skills 的宿主；
- 可运行 `npx` 的 Node.js 环境；
- 系统 Git。

完全没有 Git 时，Auto Git 自身尚未安装，不能先运行 doctor。应由当前宿主 Agent
读取操作系统事实，生成官方/受信任包管理器的 Git 安装计划；用户确认后安装，并以
`git --version` 和 PATH 复验。随后才执行下面的标准 Skill 安装命令。

验证依据：

- [标准 Skills CLI README](https://github.com/vercel-labs/skills/blob/main/README.md)
- [安装来源分流](https://github.com/vercel-labs/skills/blob/main/src/add.ts)
- [Git clone 实现](https://github.com/vercel-labs/skills/blob/main/src/git.ts)

GitHub 主源的项目级安装：

> GitHub已有备份记录；本轮未验证安装源实时可用性，安全候选也尚未推送。
> 安装试用仍待验收。出现“repository not found”时先核对来源与权限，不替换为同名仓库。

```bash
npx skills add wukongai/auto-git
```

用户明确要求多个项目都能使用时，才生成 Global 安装计划：

```bash
npx skills add wukongai/auto-git -g -a codex -a claude-code
```

- `-g` 是用户级范围；
- `-a codex` 暴露给 Codex；
- `-a claude-code` 暴露给 Claude Code；WorkBuddy 复用 Claude Code 通道。

Gitee 镜像必须与 GitHub 主源指向相同版本和 Commit。真实 Gitee Owner、URL 尚未通过
首次建库和远端 OID 验证前，不生成可执行安装命令，也不猜测同名仓库。

升级和卸载使用标准 Skills CLI：

```bash
npx skills update auto-git
npx skills remove auto-git
```

安装器负责 project/global 路径、软链接或复制、升级 ownership 和卸载。Auto Git 在
安装后验证 Skill discovery、版本、contract 和 bundled scripts；不能只凭文件存在
报告成功。

## 没有系统 Git 时

Skill 获取和系统 Git 安装是两个阶段，但顺序不能倒置：当前标准仓库安装路径需要先
有 Git，之后才能获取 Auto Git。首装 Git 由宿主 Agent + 系统官方入口指导；Auto Git
安装后再由自己的 doctor 复验并接管后续项目。不得声称 Auto Git 能在尚未安装时自行
安装 Git，也不以私有安装器掩盖前置条件。

## Python、Git、GitHub CLI

先运行 doctor，按 capability 而不是 PATH 猜测判断：

- Python 必须为 3.11+；脚本运行时只依赖标准库。
- Git 缺失时给出系统官方或受信任包管理器步骤，显示是否需要管理员权限，安装后运行
  `git --version` 和 PATH 复验。
- GitHub CLI 只在 GitHub 登录、仓库创建和 Release 时需要；安装后运行 `gh --version`。
- `0.1.0` 不自动执行 root/admin 安装，不修改系统 PATH，不把安装成功当成认证成功。

GitHub 登录使用 `gh auth login` 的浏览器/设备流程。Auto Git 不接收、打印或保存 Token。
