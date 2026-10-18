#!/usr/bin/env python3
"""
PreToolUse(Bash) hook —— 自动放行本仓库项目脚本，根治脚本调用弹窗（减弹窗主力）

为什么需要它：
  allowlist 是「前缀匹配」，但项目脚本常被绝对路径或 worktree 内路径调用，
  相对前缀完全对不上 → 永远弹窗。本 hook 直接 approve「真实存在的项目脚本」，
  跳过权限弹窗。

放行边界（同时满足才放行）：
  1. 调用形态是「脚本路径」或「launcher + 脚本路径」
     - 直接调用：scripts/foo.sh / ./scripts/foo.sh / scripts/ank-status（可无扩展名）
     - launcher：bash/sh/zsh/python/python3/node + 脚本路径
  2. 脚本逻辑路径落在 scripts/** 或 .claude/hooks/** 下
     （兼容任意 worktree 前缀：.worktrees/<wt>/、.agents/worktrees/<wt>/ 等）
  3. 脚本必须在本项目根目录内（绝对路径规范化后校验）
  4. 脚本文件必须真实存在（防止指向不存在路径绕过）

不放行：
  - ad-hoc 命令（bash -c "..." / python -c "..." / -m 模块）
  - 复合命令不由本 hook 判断；需要时交给用户确认或可选的命令风格检查
  - 危险 rm 由 protect-dangerous-rm.py 独立扫全命令兜底（approve 不覆盖 exit 2）

输出协议：
  - stdout 输出 {"decision":"approve","reason":"..."} = 跳过 allowlist 弹窗
  - exit 0 + 无 stdout = 不干预，走默认权限检查
  - 任何异常一律 exit 0 静默放行（永不阻塞工作流）
"""
import json
import os
import re
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    cmd = data.get("tool_input", {}).get("command", "")
    if not cmd or not cmd.strip():
        sys.exit(0)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "").rstrip("/")
    if not project_dir:
        sys.exit(0)

    # 提取脚本路径：命令首 token，或 launcher 后的次 token
    tokens = cmd.lstrip().split(None, 2)
    if not tokens:
        sys.exit(0)

    first = tokens[0]
    LAUNCHERS = {"bash", "sh", "zsh", "node",
                 "python", "python3",
                 "python3.10", "python3.11", "python3.12", "python3.13"}
    if first in LAUNCHERS:
        if len(tokens) < 2:
            sys.exit(0)
        script_path = tokens[1]
    else:
        script_path = first

    # 拒绝选项参数（-c / -m / -lic 等），这类是 ad-hoc 命令不是脚本
    if script_path.startswith("-"):
        sys.exit(0)

    # 规范成绝对路径
    if script_path.startswith("/"):
        abs_path = os.path.normpath(script_path)
    else:
        abs_path = os.path.normpath(os.path.join(project_dir, script_path))

    # 必须落在项目根目录下（含 worktree）
    if not abs_path.startswith(project_dir + os.sep):
        sys.exit(0)

    rel = abs_path[len(project_dir) + 1:]

    # 逻辑路径必须是 scripts/** 或 .claude/hooks/** 下的脚本。
    # 用 (^|/) 锚点吸收任意 worktree 前缀（.worktrees/<wt>/、.agents/worktrees/<wt>/）。
    valid = (
        re.search(r"(^|/)scripts/[\w\-./]+$", rel)
        or re.search(r"(^|/)\.claude/hooks/[\w\-.]+\.(sh|py)$", rel)
    )
    if not valid:
        sys.exit(0)

    # 文件必须真实存在
    if not os.path.isfile(abs_path):
        sys.exit(0)

    print(json.dumps(
        {"decision": "approve", "reason": f"项目脚本自动放行：{rel}"},
        ensure_ascii=False,
    ))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
