"""只恢复 Auto Git 拥有且未漂移的 index 备份。"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .planner import create_plan
from .runner import run
from .state import read_json


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_dir(repo: Path) -> Path:
    git_dir = Path(run(["git", "rev-parse", "--git-dir"], cwd=repo).stdout.strip())
    if not git_dir.is_absolute():
        git_dir = repo / git_dir
    return git_dir


def _index_checksum(repo: Path) -> str:
    index = _git_dir(repo) / "index"
    return _sha256(index) if index.is_file() else "missing"


def _atomic_replace_from(source: Path, target: Path) -> None:
    """同目录完整写入、fsync、校验后原子替换目标文件。"""
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.auto-git-",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            with source.open("rb") as source_handle:
                shutil.copyfileobj(source_handle, handle)
            handle.flush()
            os.fsync(handle.fileno())
        if _sha256(temporary) != _sha256(source):
            raise RuntimeError("原子恢复临时文件 checksum 不一致")
        os.replace(temporary, target)
        directory_fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def _require_direct_child(path: Path, parent: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.parent != parent.expanduser().resolve():
        raise RuntimeError(f"{label} 不属于 Auto Git 状态目录")
    return resolved


def create_recovery_plan(
    record_path: Path,
    *,
    repo: Path,
    state_home: Path,
) -> dict[str, Any]:
    """从受管 operation record 创建单独审批的 index 恢复计划。"""
    records_home = state_home / "records"
    resolved_record = _require_direct_child(record_path, records_home, "恢复记录")
    if not resolved_record.is_file():
        raise RuntimeError("恢复记录不存在")
    record = read_json(resolved_record)
    if not isinstance(record, dict):
        raise RuntimeError("恢复记录格式无效")
    if (
        record.get("schema_version") != "1"
        or record.get("status") != "succeeded"
        or record.get("action") != "stage_commit"
        or record.get("owned") is not True
    ):
        raise RuntimeError("恢复记录不属于可恢复的 Auto Git Commit")

    plan_id = record.get("plan_id")
    if not isinstance(plan_id, str) or resolved_record.name != f"{plan_id}.json":
        raise RuntimeError("恢复记录 plan_id 与文件身份不一致")
    resolved_repo = repo.expanduser().resolve()
    if Path(str(record.get("repo", ""))).expanduser().resolve() != resolved_repo:
        raise RuntimeError("恢复记录 repo 与目标仓库不一致")

    expected_backup = (state_home / "index-backups" / f"{plan_id}.index").resolve()
    details = record.get("details")
    if not isinstance(details, dict):
        raise RuntimeError("恢复记录缺少 details")
    backup_value = details.get("index_backup")
    if not backup_value or Path(str(backup_value)).expanduser().resolve() != expected_backup:
        raise RuntimeError("恢复记录的 index 备份身份不一致")
    if not expected_backup.is_file():
        raise RuntimeError("index 备份不存在")

    checksum_file = expected_backup.with_suffix(f"{expected_backup.suffix}.sha256")
    if not checksum_file.is_file():
        raise RuntimeError("index 备份 checksum 缺失")
    actual_backup_checksum = _sha256(expected_backup)
    recorded_checksum = details.get("index_backup_checksum")
    if (
        checksum_file.read_text(encoding="ascii").strip() != actual_backup_checksum
        or recorded_checksum != actual_backup_checksum
    ):
        raise RuntimeError("index 备份 checksum 已漂移")

    current_checksum = _index_checksum(resolved_repo)
    if current_checksum != details.get("post_index_checksum"):
        raise RuntimeError("当前 index 已漂移，拒绝覆盖用户暂存区")

    return create_plan(
        "recover_index",
        resolved_repo,
        {
            "record_path": str(resolved_record),
            "record_plan_id": plan_id,
            "index_backup": str(expected_backup),
            "index_backup_checksum": actual_backup_checksum,
            "expected_current_index_checksum": current_checksum,
        },
    )


def restore_index(
    repo: Path,
    params: dict[str, Any],
    *,
    state_home: Path,
    recovery_plan_id: str,
) -> dict[str, Any]:
    """在 plan 审批、仓库锁和双重 checksum 后恢复 index，并留下撤销备份。"""
    source_plan_id = params.get("record_plan_id")
    if not isinstance(source_plan_id, str) or not source_plan_id:
        raise RuntimeError("恢复计划缺少来源 plan_id")
    expected_backup = (state_home / "index-backups" / f"{source_plan_id}.index").resolve()
    backup = Path(str(params.get("index_backup", ""))).expanduser().resolve()
    if backup != expected_backup or not backup.is_file():
        raise RuntimeError("恢复计划的 index 备份身份无效")
    checksum_file = backup.with_suffix(f"{backup.suffix}.sha256")
    if not checksum_file.is_file():
        raise RuntimeError("index 备份 checksum 缺失")
    actual_backup_checksum = _sha256(backup)
    if (
        actual_backup_checksum != params.get("index_backup_checksum")
        or checksum_file.read_text(encoding="ascii").strip() != actual_backup_checksum
    ):
        raise RuntimeError("index 备份 checksum 已漂移")
    if _index_checksum(repo) != params.get("expected_current_index_checksum"):
        raise RuntimeError("当前 index 已漂移，拒绝覆盖用户暂存区")

    index = _git_dir(repo) / "index"
    undo = (state_home / "recovery-undo" / f"{recovery_plan_id}.index").resolve()
    undo.parent.mkdir(parents=True, exist_ok=True)
    if index.is_file():
        shutil.copy2(index, undo)
        undo.with_suffix(f"{undo.suffix}.sha256").write_text(
            _sha256(undo) + "\n",
            encoding="ascii",
        )
    _atomic_replace_from(backup, index)
    if _sha256(index) != actual_backup_checksum:
        compensated = False
        if undo.is_file():
            try:
                _atomic_replace_from(undo, index)
                compensated = _sha256(index) == _sha256(undo)
            except (OSError, RuntimeError):
                compensated = False
        raise RuntimeError(
            "index 恢复 postflight 失败；"
            + ("已恢复操作前 index" if compensated else "自动补偿失败，状态未知")
        )
    return {
        "restored": True,
        "source_plan_id": source_plan_id,
        "restored_index_checksum": actual_backup_checksum,
        "undo_backup": str(undo) if undo.is_file() else None,
    }
