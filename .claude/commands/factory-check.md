# Factory Check

Run this before calling a feature-level task done.

## Checklist

1. Read `docs/constitution.md`.
2. Check changed files with `git status --short`.
3. Confirm docs alignment:
   - spec / plan for feature work
   - test plan for risky work
   - daily log for meaningful work
   - handoff if the task continues later
   - OB task / external board sync if enabled
4. Run the project verification command:

```bash
python3 -m pytest -q
ruff check --no-cache scripts tests
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q scripts
```

5. Run credential lint if installed:

```bash
bash scripts/credential-lint.sh --all
```

6. If `.ai-native/profile.json` declares `skillhub_enabled=true`, verify skill entrypoints:

```bash
PROJECT_ROOT="$(pwd)"
cd "/Users/aim5/Documents/CodingProject/agent-skill-hub" && PYTHONPATH=src python3 -m skillhub.cli diff --profile "auto-git" --project "$PROJECT_ROOT"
```

当前 profile 声明 `skillhub_enabled=false`，因此记录 `skillhub: skipped`；未来启用后才运行
上面的 diff。启用后出现 missing skill entrypoints 是 FAIL，不是 WARN。

Report PASS / WARN / FAIL with skipped checks and reasons.
