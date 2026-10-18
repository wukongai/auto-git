"""Skill Release 归档的 manifest 与 SHA-256 验证。"""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Any, Sequence


def _safe_file(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"归档路径不安全：{relative}")
    path = root.joinpath(*pure.parts).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"归档路径越界：{relative}") from exc
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"归档文件不存在或是链接：{relative}")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(root: Path, files: Sequence[str]) -> dict[str, Any]:
    """为显式文件集合生成稳定清单。"""
    normalized = sorted(set(files))
    if not normalized:
        raise ValueError("manifest 文件集合不能为空")
    entries = []
    for relative in normalized:
        path = _safe_file(root, relative)
        entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return {"schema_version": "1", "algorithm": "sha256", "files": entries}


def verify_manifest(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    failures = []
    if manifest.get("schema_version") != "1" or manifest.get("algorithm") != "sha256":
        failures.append("manifest 契约不受支持")
    for entry in manifest.get("files", []):
        try:
            path = _safe_file(root, str(entry["path"]))
        except (ValueError, KeyError) as exc:
            failures.append(str(exc))
            continue
        if path.stat().st_size != entry.get("size") or _sha256(path) != entry.get("sha256"):
            failures.append(f"文件校验失败：{entry.get('path')}")
    return {"schema_version": "1", "verified": not failures, "failures": failures}
