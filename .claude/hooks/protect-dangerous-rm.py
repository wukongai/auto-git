#!/usr/bin/env python3
"""
PreToolUse(Bash) hook —— 危险 rm 兜底拦截（独立守卫·防御纵深）
退出码 2 = 阻止操作，stderr 反馈给 Claude；exit 0 = 放行。

为什么独立扫全命令：
  复合白名单可能放行 `scripts/x.sh && rm -rf /` 这类「正经脚本 + 尾随危险命令」。
  本 hook 不管命令的复合结构，直接在整条命令文本里搜危险 rm 模式 → 闭合此洞。
  deny 列表只能枚举字面量，难穷举；hook 用规则判定更稳。

判定为危险并阻断的 rm：
  - rm -rf / 、rm -rf /*               （清根）
  - rm -rf ~ 、rm -rf ~/ 、rm -rf $HOME（清家目录）
  - rm -rf <绝对路径>，且该绝对路径不在本项目根目录内（清项目外）

放行（项目内清理是日常）：
  - 相对路径：rm -rf dist / node_modules/.cache / .next / tmp
  - 本项目根目录内的绝对路径

异常一律 exit 0 静默放行，绝不阻塞工作流。
"""
import json
import os
import re
import sys


def is_dangerous(cmd, project_dir):
    # 是否含递归强制删除标志：-rf / -fr / -r -f / --recursive --force
    if not re.search(r"\brm\b", cmd):
        return None
    if not re.search(r"\brm\b[^\n;&|]*?(-\w*r\w*f|\-\w*f\w*r|-r\b[^\n;&|]*-f|-f\b[^\n;&|]*-r|--recursive|--force)", cmd):
        # 没有 -r/-f 组合，普通 rm 单文件，不在本 hook 拦截范围
        return None

    # 清根 / 清家目录字面量
    if re.search(r"\brm\b[^\n;&|]*\s(/|/\*)(\s|$)", cmd):
        return "rm 目标为根目录 /"
    if re.search(r"\brm\b[^\n;&|]*\s(~|~/|\$HOME)(\s|/|$)", cmd):
        return "rm 目标为家目录 ~ / $HOME"

    # 逐个绝对路径目标校验：必须落在项目根内
    for m in re.finditer(r"(?<!\S)(/[^\s;&|]+)", cmd):
        target = m.group(1)
        # 只校验出现在 rm 命令片段里的绝对路径（粗略：整条命令含 rm 即视为相关）
        norm = os.path.normpath(target)
        if norm == "/" :
            return "rm 目标为根目录 /"
        if project_dir and not (norm == project_dir or norm.startswith(project_dir + os.sep)):
            # 项目外绝对路径
            # 放过常见安全临时区，避免误伤
            if not (norm.startswith("/tmp/") or norm.startswith("/private/tmp/") or norm.startswith("/var/folders/")):
                return f"rm 目标在项目外：{target}"
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    cmd = data.get("tool_input", {}).get("command", "")
    if not cmd:
        sys.exit(0)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "").rstrip("/")

    reason = is_dangerous(cmd, project_dir)
    if reason:
        print(f"""⛔ 已阻止：危险 rm 命令（{reason}）

原文：{cmd[:300]}

这类删除可能波及根目录 / 家目录 / 本项目之外，不可逆。
- 若确需删项目内文件 → 用相对路径或本项目根内的绝对路径
- 若确需删项目外文件 → 请用户手动执行，agent 不替用户做项目外破坏性删除
""", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
