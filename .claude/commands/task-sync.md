# Task Sync

Use this before calling project work done when OB task or an external board is part of the workflow.

## Steps

1. Read `.ai-native/profile.json` for:
   - `task_sync_enabled`
   - `task_system`
   - `task_vault`
   - `task_parent_project`
   - `task_sync_command`
2. Check whether an existing task already represents this work.
3. Update the existing task when possible; create only if no matching task exists.
4. Include delivery links, daily log/handoff link, verification, and retrospective.
5. Keep machine-readable output when supported.

## Project Command

```bash
python3 /Users/aim5/Documents/CodingProject/feishukanban-ob-sync/sync.py --create-task --vault /Users/aim5/Documents/OB --json
```

## Report

Return task path, record ID, URL, status, and any sync failure.
