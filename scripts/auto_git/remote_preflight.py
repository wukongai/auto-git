"""构建可批准的远程事实，写入前按同一目标重新核验。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .remote import RemoteError, _branch, _validate_branch, normalize_remote_url, validate_remote_name
from .runner import CommandError, run


_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def _head(repo: Path) -> str | None:
    """初始仓库尚无提交时返回空值，不虚构 HEAD。"""
    result = run(["git", "rev-parse", "--verify", "HEAD^{commit}"], cwd=repo, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _urls(repo: Path, name: str) -> tuple[str, str, str]:
    """只接受单一、已验证且 fetch/Push 一致的目标身份。"""
    fetch_urls = run(["git", "remote", "get-url", "--all", "--", name], cwd=repo).stdout.splitlines()
    push_urls = run(["git", "remote", "get-url", "--push", "--all", "--", name], cwd=repo).stdout.splitlines()
    if len(fetch_urls) != 1 or len(push_urls) != 1:
        raise RemoteError("多个 Remote endpoint 需要分别预览，拒绝合并批准")
    fetch_identity = normalize_remote_url(fetch_urls[0])
    push_identity = normalize_remote_url(push_urls[0])
    if fetch_identity != push_identity:
        raise RemoteError("fetch 与 Push 目标身份不一致，需要重新确认独立目标")
    return fetch_urls[0], push_urls[0], push_identity


def _refs(repo: Path, url: str, branch: str | None = None) -> dict[str, str]:
    """直接读取实际 endpoint，仅保存 ref/OID，不保存认证输出。"""
    argv = ["git", "ls-remote", "--refs", "--", url]
    if branch is not None:
        argv.append(f"refs/heads/{branch}")
    try:
        result = run(argv, cwd=repo)
    except CommandError as exc:
        raise RemoteError("无法读取远端最新引用，拒绝使用缓存事实") from exc
    refs: dict[str, str] = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 2 or not _OID.fullmatch(fields[0]) or not fields[1].startswith("refs/"):
            raise RemoteError("远端引用格式无效，无法形成批准事实")
        if fields[1] in refs and refs[fields[1]] != fields[0]:
            raise RemoteError("远端引用重复且 OID 冲突")
        refs[fields[1]] = fields[0]
    return dict(sorted(refs.items()))


def build_push_preflight(repo: Path, name: str, branch: str) -> dict[str, Any]:
    """固定将公开的完整 Commit 清单及本地/远端事实。"""
    repo = Path(repo).expanduser().resolve()
    name = validate_remote_name(repo, name, require_configured=True)
    branch = _validate_branch(repo, branch)
    if _branch(repo) != branch:
        raise RemoteError("当前分支与 Push 计划不一致")
    local_head = _head(repo)
    if local_head is None:
        raise RemoteError("尚无已提交 HEAD，不能生成 Push 计划")
    _, push_url, identity = _urls(repo, name)
    try:
        run(["git", "fetch", "--prune", "--", name], cwd=repo)
    except CommandError as exc:
        raise RemoteError("远端 fetch 失败，拒绝使用旧事实") from exc
    remote_oid = _refs(repo, push_url, branch).get(f"refs/heads/{branch}")
    if remote_oid is not None:
        known = run(["git", "cat-file", "-e", f"{remote_oid}^{{commit}}"], cwd=repo, check=False)
        if known.returncode:
            try:
                run(["git", "fetch", "--no-tags", "--", push_url, f"refs/heads/{branch}"], cwd=repo)
            except CommandError as exc:
                raise RemoteError("无法获取远端提交事实") from exc
            if _refs(repo, push_url, branch).get(f"refs/heads/{branch}") != remote_oid:
                raise RemoteError("远端在预检期间变化，请重新预览")
    revision = f"{remote_oid}..{local_head}" if remote_oid else local_head
    commits = run(["git", "rev-list", "--reverse", "--topo-order", revision], cwd=repo).stdout.splitlines()
    behind = int(run(["git", "rev-list", "--count", f"{local_head}..{remote_oid}"], cwd=repo).stdout) if remote_oid else 0
    if behind:
        raise RemoteError("远端领先或已分叉，拒绝 Push 计划")
    if _head(repo) != local_head or _branch(repo) != branch or _urls(repo, name)[2] != identity:
        raise RemoteError("本地或目标在预检期间漂移，请重新预览")
    return {
        "schema_version": "1",
        "kind": "push",
        "repo": str(repo),
        "remote": name,
        "branch": branch,
        "url_identity": identity,
        "fetch_url_identity": identity,
        "push_url_identity": identity,
        "local_head": local_head,
        "remote_oid": remote_oid,
        "ahead": len(commits),
        "behind": behind,
        "diverged": False,
        "commits": commits,
        "status": "already_synced" if remote_oid == local_head else "ready",
    }


def _require_snapshot(repo: Path, snapshot: dict[str, Any], kind: str) -> Path:
    """拒绝不同仓库、动作及结构的预检资料。"""
    repo = Path(repo).expanduser().resolve()
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("schema_version") != "1"
        or snapshot.get("kind") != kind
        or snapshot.get("repo") != str(repo)
        or not isinstance(snapshot.get("remote"), str)
    ):
        raise RemoteError("远程预检身份或结构无效，请重新预览")
    return repo


def validate_push_preflight(repo: Path, snapshot: dict[str, Any]) -> None:
    """重新获取最新远程事实，拒绝沿用漂移后的批准。"""
    repo = _require_snapshot(repo, snapshot, "push")
    if not isinstance(snapshot.get("branch"), str):
        raise RemoteError("远程预检缺少分支，请重新预览")
    current = build_push_preflight(repo, snapshot["remote"], snapshot["branch"])
    if current != snapshot:
        raise RemoteError("远程批准事实已漂移，请重新预览")


def _history(repo: Path, local_head: str | None, refs: dict[str, str]) -> str:
    """只以本地已有对象证明共同历史，不猜测未知远端的祖先。"""
    if not refs:
        return "empty"
    branches = [oid for ref, oid in refs.items() if ref.startswith("refs/heads/")]
    if not local_head or not branches:
        return "unknown"
    for oid in branches:
        common = run(["git", "merge-base", local_head, oid], cwd=repo, check=False)
        if common.returncode or not common.stdout.strip():
            return "unknown"
    return "related"


def build_connection_preflight(repo: Path, name: str, url: str) -> dict[str, Any]:
    """连接前只读分类空库、已证明相关历史和未知历史。"""
    repo = Path(repo).expanduser().resolve()
    name = validate_remote_name(repo, name, require_configured=False)
    identity = normalize_remote_url(url)
    configured = name in run(["git", "remote"], cwd=repo).stdout.splitlines()
    if configured and _urls(repo, name)[2] != identity:
        raise RemoteError("现有 Remote URL 与计划不一致")
    local_head = _head(repo)
    refs = _refs(repo, url)
    return {
        "schema_version": "1",
        "kind": "remote_connect",
        "repo": str(repo),
        "remote": name,
        "url_identity": identity,
        "transport_url": url,
        "configured": configured,
        "local_head": local_head,
        "remote_refs": refs,
        "history": _history(repo, local_head, refs),
    }


def validate_connection_preflight(repo: Path, snapshot: dict[str, Any]) -> None:
    """连接写入前重读目标和引用，不覆盖旧 Remote 或忽略新历史。"""
    repo = _require_snapshot(repo, snapshot, "remote_connect")
    if not isinstance(snapshot.get("transport_url"), str):
        raise RemoteError("连接预检缺少目标，请重新预览")
    current = build_connection_preflight(repo, snapshot["remote"], snapshot["transport_url"])
    if current != snapshot:
        raise RemoteError("远程连接事实已漂移，请重新预览")
