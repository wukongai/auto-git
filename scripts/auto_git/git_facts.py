"""读取 Git 机器事实，不从聊天猜测仓库状态。"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Any

from .runner import run
from .schema import SCHEMA_VERSION, hash_payload


def parse_porcelain_v2_z(raw: bytes) -> dict[str, Any]:
    """解析 `git status --porcelain=v2 -z --branch` 的关键字段。"""
    branch: str | None = None
    oid: str | None = None
    changes: list[dict[str, str]] = []
    records = raw.split(b"\0")
    index = 0
    while index < len(records):
        record = records[index].decode("utf-8", errors="surrogateescape")
        index += 1
        if not record:
            continue
        if record.startswith("# branch.head "):
            branch = record.removeprefix("# branch.head ")
            continue
        if record.startswith("# branch.oid "):
            oid = record.removeprefix("# branch.oid ")
            continue
        if record.startswith("? "):
            changes.append({"kind": "untracked", "path": record[2:]})
            continue
        if record.startswith("! "):
            changes.append({"kind": "ignored", "path": record[2:]})
            continue
        if record.startswith("1 "):
            fields = record.split(" ", 8)
            changes.append(
                {"kind": "ordinary", "xy": fields[1], "path": fields[8]}
            )
            continue
        if record.startswith("2 "):
            fields = record.split(" ", 9)
            original = ""
            if index < len(records):
                original = records[index].decode(
                    "utf-8", errors="surrogateescape"
                )
                index += 1
            changes.append(
                {
                    "kind": "renamed",
                    "xy": fields[1],
                    "path": fields[9],
                    "original_path": original,
                }
            )
            continue
        if record.startswith("u "):
            fields = record.split(" ", 10)
            changes.append({"kind": "unmerged", "xy": fields[1], "path": fields[10]})
    return {"branch": branch, "oid": oid, "changes": changes}


def _directory_fingerprint(path: Path) -> str:
    entries: list[tuple[Any, ...]] = []
    for item in sorted(
        path.rglob("*"),
        key=lambda value: value.relative_to(path).as_posix(),
    ):
        relative = item.relative_to(path)
        if relative.parts and relative.parts[0] == ".git":
            continue
        metadata = item.lstat()
        if item.is_symlink():
            kind = "symlink"
            target = os.readlink(item)
        elif item.is_dir():
            kind = "directory"
            target = None
        elif item.is_file():
            kind = "file"
            target = None
        else:
            kind = "other"
            target = None
        entries.append(
            (
                relative.as_posix(),
                kind,
                stat.S_IMODE(metadata.st_mode),
                metadata.st_size,
                metadata.st_mtime_ns,
                target,
            )
        )
    return hash_payload({"root": str(path.resolve()), "entries": entries})


def _update_path_digest(digest: Any, root: Path, relative_value: str) -> None:
    """把工作区路径身份和内容送入摘要，不向 facts 回显文件内容。"""
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        digest.update(b"unsafe-path\0")
        digest.update(relative_value.encode("utf-8", errors="surrogateescape"))
        return
    target = root / relative
    digest.update(b"path\0")
    digest.update(relative_value.encode("utf-8", errors="surrogateescape"))
    digest.update(b"\0")
    try:
        mode = stat.S_IMODE(target.lstat().st_mode)
    except FileNotFoundError:
        digest.update(b"missing\0")
        return
    digest.update(f"mode:{mode:o}\0".encode("ascii"))
    # 凭证形态路径只取元数据；盘点不能为摘要而打开私有正文。
    from .sensitive_paths import is_sensitive_path
    if is_sensitive_path(relative_value):
        metadata = target.lstat()
        digest.update(f"sensitive-metadata:{metadata.st_size}:{metadata.st_mtime_ns}\0".encode("ascii"))
        return
    if target.is_symlink():
        digest.update(b"symlink\0")
        digest.update(os.readlink(target).encode("utf-8", errors="surrogateescape"))
        return
    if not target.is_file():
        digest.update(b"non-file\0")
        return
    digest.update(b"file\0")
    with target.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)


def inspect_repo(path: Path | str) -> dict[str, Any]:
    """返回版本化 facts 和能检测工作区漂移的 fingerprint。"""
    repo = Path(path).expanduser().resolve()
    probe = run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=repo,
        check=False,
    )
    if probe.returncode:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "path": str(repo),
            "is_repo": False,
            "branch": None,
            "head": None,
            "changes": [],
            "operation": None,
        }
        payload["fingerprint"] = _directory_fingerprint(repo)
        return payload

    root = Path(probe.stdout.strip()).resolve()
    status = run(
        ["git", "status", "--porcelain=v2", "-z", "--branch", "--untracked-files=all"],
        cwd=root,
    )
    parsed = parse_porcelain_v2_z(status.stdout.encode("utf-8", errors="surrogateescape"))
    git_dir = Path(run(["git", "rev-parse", "--git-dir"], cwd=root).stdout.strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    operation = None
    for marker, label in (
        ("MERGE_HEAD", "merge"),
        ("rebase-merge", "rebase"),
        ("rebase-apply", "rebase"),
        ("CHERRY_PICK_HEAD", "cherry-pick"),
    ):
        if (git_dir / marker).exists():
            operation = label
            break
    index = run(["git", "ls-files", "--stage", "-z"], cwd=root)
    effective_config = run(
        [
            "git",
            "config",
            "--null",
            "--list",
            "--show-origin",
            "--show-scope",
        ],
        cwd=root,
        check=False,
    )
    fingerprint_digest = hashlib.sha256()
    for label, value in (
        ("status", status.stdout),
        ("head", parsed["oid"] or ""),
        ("index", index.stdout),
        ("effective-config", effective_config.stdout),
        ("operation", operation or ""),
    ):
        fingerprint_digest.update(label.encode("ascii"))
        fingerprint_digest.update(b"\0")
        fingerprint_digest.update(value.encode("utf-8", errors="surrogateescape"))
        fingerprint_digest.update(b"\0")
    changed_paths = {
        value
        for change in parsed["changes"]
        for key in ("path", "original_path")
        if isinstance((value := change.get(key)), str) and value
    }
    if (root / ".auto-git.toml").exists():
        changed_paths.add(".auto-git.toml")
    for relative_value in sorted(changed_paths):
        _update_path_digest(fingerprint_digest, root, relative_value)
    fingerprint = fingerprint_digest.hexdigest()
    return {
        "schema_version": SCHEMA_VERSION,
        "path": str(root),
        "is_repo": True,
        "branch": parsed["branch"],
        "head": parsed["oid"],
        "changes": parsed["changes"],
        "operation": operation,
        "fingerprint": fingerprint,
    }
