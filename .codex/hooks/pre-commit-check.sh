#!/usr/bin/env bash
set -euo pipefail

payload="$(cat || true)"

if printf '%s' "$payload" | grep -E 'git add -A|git add \.|git push --force|git reset --hard|git clean -fd' >/dev/null; then
  cat >&2 <<'MSG'
Blocked by ai-native harness: unsafe git command.
Use explicit file paths for staging and ask before destructive git operations.
MSG
  exit 2
fi

if printf '%s' "$payload" | grep -E 'git push( |$)' >/dev/null; then
  cat >&2 <<'MSG'
Reminder: push requires local verification and explicit user approval.
If approval is not already present in the current task context, stop and ask.
MSG
fi

exit 0
