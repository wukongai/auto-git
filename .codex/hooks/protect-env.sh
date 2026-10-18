#!/usr/bin/env bash
# PreToolUse(Edit|Write) hook —— 拦截 .env / 凭证写入（凭证红线）
# 退出码 2 = 阻止操作，stderr 反馈给 Claude；exit 0 = 放行。
set -euo pipefail

payload="$(cat || true)"

# 命中 .env 文件名，或内容含密钥样式（私钥块 / sk- / ghp_）→ 阻断
if printf '%s' "$payload" | grep -E '(\.env(\.|"|$)|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36})' >/dev/null; then
  cat >&2 <<'MSG'
🚫 已阻止：检测到 .env / 凭证文件或密钥样式内容的写入。
凭证只能进私有层（Keychain / 用户级 MCP 配置 / SSH config / 仓库外环境变量）。
请告诉用户需要新增哪个变量，由用户手动编辑。
MSG
  exit 2
fi

exit 0
