"""本地状态目录、原子写和仓库互斥锁。"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_state_home() -> Path:
    override = os.environ.get("AUTO_GIT_STATE_HOME")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AutoGit"
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "auto-git"


def atomic_write_json(path: Path, payload: Any) -> None:
    """同目录临时文件 + replace，避免半写状态。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def operation_history(repo: Path, state_home: Path) -> dict[str, Any]:
    """列出属于目标仓库的紧凑 operation 记录，不暴露命令输出或凭证。"""
    resolved_repo = repo.expanduser().resolve()
    records_home = state_home.expanduser().resolve() / "records"
    operations: list[dict[str, Any]] = []
    invalid_records = 0
    if records_home.is_dir():
        for path in records_home.glob("*.json"):
            try:
                record = read_json(path)
            except (OSError, json.JSONDecodeError):
                invalid_records += 1
                continue
            if (
                not isinstance(record, dict)
                or Path(str(record.get("repo", ""))).expanduser().resolve()
                != resolved_repo
            ):
                continue
            details = record.get("details")
            if not isinstance(details, dict):
                details = {}
            operations.append(
                {
                    "plan_id": record.get("plan_id"),
                    "action": record.get("action"),
                    "status": record.get("status"),
                    "completed_at": record.get("completed_at"),
                    "commit_oid": details.get("head"),
                    "recovery_available": bool(details.get("index_backup")),
                    "next_step": record.get("next_step"),
                }
            )
    operations.sort(key=lambda item: str(item.get("completed_at") or ""), reverse=True)
    return {
        "schema_version": "1",
        "repo": str(resolved_repo),
        "operations": operations,
        "invalid_records": invalid_records,
        "writes_performed": False,
    }


class RepositoryLock:
    """用 O_EXCL 创建轻量跨进程锁。"""

    def __init__(
        self,
        path: Path,
        *,
        action: str | None = None,
        repo: Path | None = None,
    ):
        self.path = path
        self.action = action
        self.repo = repo
        self._held = False

    def _collision_message(self) -> str:
        try:
            metadata = read_json(self.path)
            pid = int(metadata["pid"])
            started_at = str(metadata["started_at"])
            action = str(metadata.get("action") or "unknown")
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return f"仓库锁已存在且元数据无效，需人工确认：{self.path}"
        try:
            os.kill(pid, 0)
            alive = True
        except ProcessLookupError:
            alive = False
        except PermissionError:
            alive = True
        if not alive:
            return (
                "检测到 stale 仓库锁，需人工确认没有执行进程后再移除："
                f"pid={pid} action={action} started_at={started_at} path={self.path}"
            )
        return (
            f"仓库锁已存在：pid={pid} action={action} "
            f"started_at={started_at} path={self.path}"
        )

    def __enter__(self) -> "RepositoryLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RuntimeError(self._collision_message()) from exc
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "pid": os.getpid(),
                    "action": self.action,
                    "repo": str(self.repo) if self.repo is not None else None,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                },
                handle,
                ensure_ascii=False,
                sort_keys=True,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._held = True
        return self

    def __exit__(self, *_args: object) -> None:
        if self._held:
            self.path.unlink(missing_ok=True)
            self._held = False
