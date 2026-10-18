---
name: script-quality
description: 脚本质量规范——把复杂脚本抽成独立文件，并用 lint + git hook 形成机器门禁
metadata:
  type: rule
---

<!-- ⚙️ 本文件由 ai-native-kit adapter 生成；修改请改 templates/_shared/ 对应模板后重跑 adapter，手改会被下次生成覆盖 -->

<!--
  【这是什么】脚本质量规范：限制 inline 脚本、长 heredoc、不可维护流水线和无 CLI 入口脚本。
  【为什么】自然语言提醒会失效；能被脚本检查的规则应进入 lint 与 git hook。
  【怎么改】项目可用 .script-quality.yml 覆盖阈值、严重度和白名单。
-->

# 脚本质量规范

## 目标

把“临时能跑”的脚本及时沉淀成“可测试、可复用、可排错”的独立文件。
自然语言规则只负责说明意图，`scripts/lint_script_quality.py` 负责提交前守门。

## 必须做

| 规则 | 要求 |
|---|---|
| 多行逻辑抽文件 | 超过 5 行的 `python -c` / `python3 -c` 必须抽到 `scripts/` 或项目约定脚本目录 |
| 长 heredoc 抽文件 | 超过 20 行的 heredoc 只适合生成 fixture / 文档样例；业务逻辑必须抽独立脚本 |
| 脚本有 CLI 入口 | `scripts/` 下可执行 Python 脚本应提供 `argparse` / `click` / `typer` / `if __name__ == "__main__"` 入口 |
| 复杂管道可追踪 | 多段 `grep | awk | sed` 等流水线应抽脚本，保留中间变量和错误输出 |
| 规则可配置 | 项目差异写入 `.script-quality.yml`，不要在 hook 里硬编码 |
| 例外显式化 | 真正的数据脚本、生成物或大 fixture 要写 allowlist 或 `lint-script-quality: skip` 理由 |

## 禁止做

| 禁止项 | 原因 |
|---|---|
| 在 agent 命令、规则文件或 skill 里堆长脚本 | 转义、换行和 shell 差异会让排错成本指数上升 |
| 在 git hook 里写业务检查逻辑 | hook 只做 dispatcher，检查逻辑必须在独立 lint 脚本里 |
| 用 `--no-verify` 当常规绕过 | 只能用于紧急修复；绕过后要补 lint 配置或修脚本 |
| 白名单无理由扩张 | 白名单是例外登记，不是关闭规则 |
| 警告长期不处理 | warning 代表技术债，不能无限期当噪音 |

## 默认配置

项目根可放 `.script-quality.yml`：

```yaml
severity:
  file-length: warning
  inline-python: error
  heredoc: warning
  missing-cli: warning
  markdown-code-block: warning
allowlist:
  large_files:
    - "content_routing.yaml"
  paths:
    - "vendor/"
inline_limits:
  python_c_max_lines: 5
  heredoc_max_lines: 20
  markdown_code_block_max_lines: 25
  file_length_max_lines: 320
```

## 例外格式

文件级临时跳过：

```text
# lint-script-quality: skip - 这是一次性迁移 fixture，2026-07-15 前拆分
```

配置级白名单：

```yaml
allowlist:
  paths:
    - "generated/"
  large_files:
    - "routing_table.yaml"
```

## 收尾自检

| 问题 | 理想答案 |
|---|---|
| 换一个 agent 执行还稳定吗 | 是，复杂逻辑在脚本文件，不依赖聊天上下文 |
| 出错时能定位到行号吗 | 是，lint 输出文件和行号 |
| 项目差异能配置吗 | 是，`.script-quality.yml` 可调整阈值和白名单 |
| hook 缺脚本会卡死吗 | 不会，dispatcher fail-open 并提示重装 |
