#!/usr/bin/env bash
set -euo pipefail

project="${CLAUDE_PROJECT_DIR:-$(pwd)}"

cat <<MSG
ai-native harness active for: $project
- Read docs/constitution.md for durable principles.
- Use AGENTS.md / CLAUDE.md for runtime rules.
- Run factory-check before calling feature work done.
MSG
