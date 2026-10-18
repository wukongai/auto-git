#!/usr/bin/env python3
"""
PreToolUse(Bash) hook —— 检测复合 Bash 命令，只警告不拦截（减弹窗软提示）
退出码恒为 0 = 永远放行；仅把改写建议写到 stderr 供参考。

⚠️ 设计修正（2026-06-15）：
  本 hook 曾用 exit 2 硬拦截所有复合命令，结果把 skill 的正常调用（如
  `curl ... | jq` 调云雾出图）一并杀死，且无优雅降级 —— 违反鲁棒性原则。
  减弹窗是「软约束」，绝不该有能力让功能性工具调用失败。故降级为只警告：
  打印改写建议，但 exit 0 放行，由模型自行决定是否改原子命令。

为什么还保留提示：
  allowlist 是前缀匹配，复合命令首 token 之后跟着子命令，前缀几乎一定对不上 → 易弹。
  保留改写建议帮助养成原子命令习惯，但不再以阻断为代价。

拦截范围：
  A. cd 复合：cd /path && cmd
  B. 管道：cmd1 | cmd2
  C. 串联：cmd1 ; cmd2 / cmd1 && cmd2 / cmd1 || cmd2

白名单（允许复合 / 放行）：
  1) 项目封装脚本调用：scripts/** 下的 .sh、.claude/hooks/** 下的 .sh/.py
     （脚本内部可自由用复合，已经过审查）
  2) stdin 接收命令（管道是唯一调用方式）：cmd | psql ... --stdin / cmd | pg_restore
  3) 引号内的特殊字符不算（git commit -m "fix: a | b"）

注意：本 hook 只管「复合结构」。危险命令（rm -rf /）由 protect-dangerous-rm.py
独立扫全命令兜底——即使复合被白名单放行也拦得住（防御纵深）。
"""
import re
import sys

INPUT = sys.stdin.read()

try:
    import json
    data = json.loads(INPUT)
    cmd = data.get("tool_input", {}).get("command", "")
except Exception:
    sys.exit(0)

if not cmd:
    sys.exit(0)


# ============ 白名单 1：项目封装脚本调用 ============
# scripts/** 下任意嵌套的 .sh，以及 .claude/hooks/** 下的 .sh/.py
WHITELIST_PREFIX_PATTERNS = [
    r"^\s*(bash\s+|sh\s+|zsh\s+)?scripts/[\w\-./]+\.sh\b",
    r"^\s*(bash\s+)?\.claude/hooks/[\w\-./]+\.sh\b",
    r"^\s*(python3?\s+)?\.claude/hooks/[\w\-./]+\.py\b",
]
for pat in WHITELIST_PREFIX_PATTERNS:
    if re.match(pat, cmd):
        sys.exit(0)


# 去掉引号内容，避免引号里的 | ; 误报（用等长占位符保留位置）
clean = re.sub(r"'[^']*'", "''", cmd)
clean = re.sub(r'"[^"]*"', '""', clean)


# ============ 白名单 2：stdin 接收命令 ============
# 管道喂给只接收 stdin 的命令是合理用法，无法拆分
STDIN_RECEIVERS = [
    r"\|\s*psql\s+[^|]*--stdin",
    r"\|\s*pg_restore\s",
]
for pat in STDIN_RECEIVERS:
    if re.search(pat, clean):
        sys.exit(0)


# ============ 检测复合标志 ============
REASONS = []

# A. cd 复合
if re.search(r"(^|[;&|]\s*)cd\s+[^;&|]+\s*(&&|\|\||;)", cmd):
    REASONS.append("cd 裸复合")
if re.search(r"(^|\s)(bash|sh|zsh)\s+(-[lic]+\s+)?[\"'][^\"']*\bcd\s+", cmd):
    REASONS.append('bash -c "cd ..." 包装复合')

# B. 管道（排除 || 和 |&）
if re.search(r"(?<!\|)\|(?![|&])", clean):
    REASONS.append("管道 |")

# C. 串联（排除 find -exec ... \;）
if re.search(r"(?<!\\);", clean):
    REASONS.append("分号 ;")
if "&&" in clean:
    REASONS.append("&&")
if "||" in clean:
    REASONS.append("||")

if not REASONS:
    sys.exit(0)

seen = set()
reasons = [r for r in REASONS if not (r in seen or seen.add(r))]

cmd_preview = cmd[:300] + ("..." if len(cmd) > 300 else "")
reasons_str = ", ".join(reasons)

print(f"""⚠️ 提示（不拦截）：检测到复合 Bash 命令（{reasons_str}）

原文：{cmd_preview}

为什么拦：复合命令首 token 之后跟着子命令，allowlist 前缀匹配几乎必弹；
参数一变又重弹。请改写为原子命令——这同时根治弹窗。

【改写为以下之一】

1) 探测多个独立信息 → 拆成多个 Bash 调用（同一 message 内并行发）
   ❌ which a ; which b ; ls | grep c
   ✅ 一条 message 发多个 Bash tool_use，各跑一条

2) 读文件 / 看片段 → 用 Read 工具
   ❌ cat /path/file | head -100      ❌ tail -50 /path/log
   ✅ Read(file_path="/path/file", limit=100, offset=0)

3) 跨仓库 / 跨 worktree → 用 git -C / 工具自带 --prefix
   ❌ cd /path && git status          ✅ git -C /path status

4) 固定 3+ 行流程 → 封成 scripts/**.sh（脚本内随便复合，自动放行）
   ❌ rm -rf dist && npm run build 2>&1 | tail -40
   ✅ scripts/build-verify.sh

5) 数据库查询 → 用 -c 单条
   ❌ echo "..." | some-cli            ✅ psql <db> -c 'SELECT ... LIMIT 5'

【白名单内不拦】
- 项目脚本：scripts/**.sh、.claude/hooks/**.{{sh,py}}
- 管道喂 stdin：cmd | psql --stdin / cmd | pg_restore
- 引号内的 | ; 不算（git commit -m "a | b"）
""", file=sys.stderr)

# 只警告，永远放行（exit 0），不阻断任何工具调用
sys.exit(0)
