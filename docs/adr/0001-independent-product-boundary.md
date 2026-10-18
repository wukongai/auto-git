# ADR 0001：Auto Git 独立产品与依赖方向

状态：Accepted（产品形态部分由 ADR 0004 修正）

日期：2026-08-02

> 2026-08-03 更新：独立产品、独立仓库与运行时低耦合决策继续有效；第 3、6 条及
> “只做 Skill”替代方案的结论由
> [ADR 0004](0004-skill-first-product-and-authoring-boundary.md) 修正。Auto Git
> 现在采用 Skill-first 形态，确定性核心随 Skill 放在 `scripts/`；Skill Engineering
> 在开发期创建和治理它。

## 背景

最初需求来自 Skill Engineering 的 Git-native 维护设想。讨论后确认，普通代码、
内容、Agent Skill 和训练营项目都面临相同问题，因此通用 Git 自动化不应只作为
Skill Engineering 的内部模块。

Auto Git 自身需要工程化初始化，但使用 ANK 初始化不应等于运行时依赖 ANK。

## 决定

1. Auto Git 位于独立目录和独立 Git 仓库：
   `/Users/aim5/Documents/CodingProject/auto-git`。
2. 仓库名和 Skill 名使用 `auto-git`；用户可见产品名使用 `Auto Git`。
3. 原决定采用“确定性本地核心/CLI + Agent Skill + 可选 hooks/CI 模板”；该产品
   形态已由 ADR 0004 修正为“Auto Git Skill + bundled deterministic scripts”。
4. Auto Git 不依赖 ANK、Skill Engineering、特定 Agent、模型 Provider 或云服务。
5. ANK 可以推荐或生成 Auto Git 接入配置；依赖方向是 `ANK → Auto Git` 的可选集成。
6. 原决定把 Skill Engineering 视为后续集成方；ADR 0004 已明确它现在是 Auto Git
   的开发期创建与治理工具，但仍不是运行时依赖。

## 结果

- Auto Git 可以独立开源、版本化、安装和被多个项目复用。
- ANK 继续专注项目工程化初始化，Auto Git 专注版本管理生命周期。
- 集成方通过稳定接口连接；接口未固定前不得提前写适配代码。

## 替代方案

- 放进 ANK：拒绝，会把 Git 产品与工程初始化生命周期绑定。
- 放进 Skill Engineering：拒绝，无法自然服务所有项目。
- 只做 Skill：原结论已被 ADR 0004 取代；确定性通过 Skill 内 `scripts/`、contract
  和回归用例保证，而不是通过第二个用户安装产品保证。
- 只做 CLI：拒绝，无法满足普通用户自然语言和训练目标。
