#!/usr/bin/env bash
# 本仓库提交门禁：只检查暂存区，不修改工作区或绕过审批。
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
bash "$ROOT/scripts/credential-lint.sh"
git diff --cached --check
