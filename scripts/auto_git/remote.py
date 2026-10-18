"""标准 Remote 连接、事实和非强制 Push。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .runner import CommandError, run


class RemoteError(RuntimeError):
    pass


_REMOTE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_SCP_REMOTE = re.compile(
    r"^(?:[A-Za-z0-9._-]+@)?(?P<host>[A-Za-z0-9.-]+):(?P<path>[^?#\s]+)$"
)
_CREDENTIAL_MARKER = re.compile(
    r"(?i)(?:ghp_|github_pat_|(?:token|password|secret)\s*[=:])"
)


def validate_remote_name(
    repo: Path,
    name: str,
    *,
    require_configured: bool,
) -> str:
    """在把 Remote 名称交给 Git 前，拒绝选项注入和歧义路径。"""
    if (
        not isinstance(name, str)
        or not name
        or not _REMOTE_NAME.fullmatch(name)
        or ".." in name
        or "//" in name
        or name.endswith("/")
        or "@{" in name
    ):
        raise RemoteError("Remote 名称无效")
    ref_check = run(
        ["git", "check-ref-format", f"refs/remotes/{name}/probe"],
        cwd=repo,
        check=False,
    )
    if ref_check.returncode:
        raise RemoteError("Remote 名称无效")
    if require_configured:
        configured = set(run(["git", "remote"], cwd=repo).stdout.splitlines())
        if name not in configured:
            raise RemoteError(f"Remote {name} 未配置")
    return name


def normalize_remote_url(url: str) -> str:
    """拒绝可持久化凭证的 URL，并返回不含用户名的稳定仓库身份。"""
    if (
        not isinstance(url, str)
        or not url.strip()
        or url != url.strip()
        or url.startswith("-")
        or any(char.isspace() for char in url)
    ):
        raise RemoteError("Remote URL 无效")
    if _CREDENTIAL_MARKER.search(url):
        raise RemoteError("Remote URL 疑似包含凭证")

    scp = _SCP_REMOTE.fullmatch(url) if "://" not in url else None
    if scp:
        return f"ssh://{scp.group('host').lower()}/{scp.group('path')}"

    parsed = urlsplit(url)
    if parsed.scheme in {"http", "https", "ssh", "git"}:
        if parsed.query:
            raise RemoteError("Remote URL 不允许 query")
        if parsed.fragment:
            raise RemoteError("Remote URL 不允许 fragment")
        embedded_password = parsed.password
        if embedded_password is not None or (
            parsed.scheme in {"http", "https"} and parsed.username is not None
        ):
            raise RemoteError("Remote URL 不允许内嵌凭证")
        if not parsed.hostname or not parsed.path.strip("/"):
            raise RemoteError("Remote URL 无效")
        port = f":{parsed.port}" if parsed.port else ""
        return (
            f"{parsed.scheme.lower()}://{parsed.hostname.lower()}{port}/"
            f"{parsed.path.lstrip('/')}"
        )
    if parsed.scheme == "file":
        file_password = parsed.password
        if parsed.query or parsed.fragment or parsed.username or file_password:
            raise RemoteError("Remote URL 不允许凭证、query 或 fragment")
        if not parsed.path:
            raise RemoteError("Remote URL 无效")
        return f"file://{Path(parsed.path).expanduser().resolve()}"
    if parsed.scheme:
        raise RemoteError("Remote URL 协议不受支持")

    local = Path(url).expanduser()
    if not local.is_absolute():
        raise RemoteError("Remote URL 必须是标准 Git URL 或绝对本地路径")
    return f"file://{local.resolve()}"


def _validate_branch(repo: Path, branch: str) -> str:
    if not isinstance(branch, str) or not branch or branch.startswith("-"):
        raise RemoteError("分支名称无效")
    check = run(["git", "check-ref-format", "--branch", branch], cwd=repo, check=False)
    if check.returncode:
        raise RemoteError("分支名称无效")
    return branch


def connect_remote(repo: Path, name: str, url: str) -> dict[str, Any]:
    name = validate_remote_name(repo, name, require_configured=False)
    url_identity = normalize_remote_url(url)
    existing = run(["git", "remote", "get-url", "--", name], cwd=repo, check=False)
    if existing.returncode == 0:
        if normalize_remote_url(existing.stdout.strip()) != url_identity:
            raise RemoteError("现有 Remote URL 与计划不一致")
        return {"name": name, "url_identity": url_identity, "changed": False}
    run(["git", "remote", "add", "--", name, url], cwd=repo)
    verified = run(["git", "remote", "get-url", "--", name], cwd=repo).stdout.strip()
    if normalize_remote_url(verified) != url_identity:
        raise RemoteError("Remote postflight 失败")
    return {"name": name, "url_identity": url_identity, "changed": True}


def _branch(repo: Path) -> str:
    value = run(["git", "branch", "--show-current"], cwd=repo).stdout.strip()
    if not value:
        raise RemoteError("detached HEAD 不允许 Push")
    return value


def remote_facts(repo: Path, name: str, branch: str | None = None) -> dict[str, Any]:
    name = validate_remote_name(repo, name, require_configured=True)
    branch = _validate_branch(repo, branch or _branch(repo))
    fetched = run(["git", "fetch", "--prune", "--", name], cwd=repo, check=False)
    if fetched.returncode:
        raise RemoteError(f"Remote {name} fetch 失败，拒绝使用旧事实")
    remote_ref = f"refs/remotes/{name}/{branch}"
    exists = run(["git", "show-ref", "--verify", remote_ref], cwd=repo, check=False)
    if exists.returncode:
        return {"name": name, "branch": branch, "exists": False, "ahead": 0, "behind": 0}
    ahead = int(
        run(["git", "rev-list", "--count", f"{remote_ref}..HEAD"], cwd=repo).stdout
    )
    behind = int(
        run(["git", "rev-list", "--count", f"HEAD..{remote_ref}"], cwd=repo).stdout
    )
    return {
        "name": name,
        "branch": branch,
        "exists": True,
        "ahead": ahead,
        "behind": behind,
        "diverged": ahead > 0 and behind > 0,
    }


def push_branch(repo: Path, name: str, branch: str) -> dict[str, Any]:
    name = validate_remote_name(repo, name, require_configured=True)
    branch = _validate_branch(repo, branch)
    if _branch(repo) != branch:
        raise RemoteError("当前分支与 Push 计划不一致")
    facts = remote_facts(repo, name, branch)
    if facts.get("behind", 0):
        raise RemoteError("远端领先或已分叉，拒绝非 fast-forward Push")
    try:
        run(
            [
                "git",
                "push",
                "--set-upstream",
                "--",
                name,
                f"HEAD:refs/heads/{branch}",
            ],
            cwd=repo,
        )
    except CommandError as exc:
        raise RemoteError("Push 失败，未使用 force") from exc
    local = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    remote = run(["git", "ls-remote", name, f"refs/heads/{branch}"], cwd=repo)
    remote_oid = remote.stdout.split()[0] if remote.stdout.split() else ""
    if remote_oid != local:
        raise RemoteError("Push 远端 postflight 不一致")
    upstream = run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        cwd=repo,
        check=False,
    ).stdout.strip()
    if upstream != f"{name}/{branch}":
        raise RemoteError("Push upstream postflight 不一致")
    return {
        "verified": True,
        "name": name,
        "branch": branch,
        "local": local,
        "remote": remote_oid,
        "upstream": upstream,
    }


def _remote_refs(repo: Path, name: str, *refs: str) -> dict[str, str]:
    """只读解析指定 Remote 的精确 ref；不保存 URL 或认证输出。"""
    name = validate_remote_name(repo, name, require_configured=True)
    result = run(["git", "ls-remote", name, *refs], cwd=repo, check=False)
    if result.returncode:
        raise RemoteError(f"无法读取 Remote {name} 的 ref")
    parsed: dict[str, str] = {}
    for line in result.stdout.splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) == 2:
            parsed[fields[1]] = fields[0]
    return parsed


def verify_mirror_refs(
    repo: Path,
    *,
    remotes: list[str],
    branch: str,
    tag: str | None = None,
) -> dict[str, Any]:
    """证明多个 Remote 的分支和可选 annotated Tag 指向同一本地事实。"""
    if len(remotes) != len(set(remotes)):
        raise RemoteError("双远程验证不允许重复 Remote")
    if len(remotes) < 2:
        raise RemoteError("双远程验证至少需要两个不同 Remote")
    branch = _validate_branch(repo, branch)
    for name in remotes:
        validate_remote_name(repo, name, require_configured=True)

    local_head = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    branch_ref = f"refs/heads/{branch}"
    branches: dict[str, str] = {}
    for name in remotes:
        remote_oid = _remote_refs(repo, name, branch_ref).get(branch_ref, "")
        if remote_oid != local_head:
            raise RemoteError(f"Remote {name} 的 branch OID 与本地 HEAD 不一致")
        branches[name] = remote_oid

    payload: dict[str, Any] = {
        "verified": True,
        "local_head": local_head,
        "branches": branches,
    }
    if tag is None:
        return payload

    from .release import validate_tag_name

    tag = validate_tag_name(repo, tag)
    tag_type = run(["git", "cat-file", "-t", tag], cwd=repo, check=False)
    if tag_type.returncode or tag_type.stdout.strip() != "tag":
        raise RemoteError("双远程版本验证只接受 annotated Tag")
    local_target = run(["git", "rev-parse", f"{tag}^{{}}"], cwd=repo).stdout.strip()
    tag_ref = f"refs/tags/{tag}"
    peeled_ref = f"{tag_ref}^{{}}"
    tags: dict[str, str] = {}
    for name in remotes:
        refs = _remote_refs(repo, name, tag_ref, peeled_ref)
        remote_target = refs.get(peeled_ref, "")
        if remote_target != local_target:
            raise RemoteError(f"Remote {name} 的 annotated Tag target 不一致")
        tags[name] = remote_target

    payload["local_tag_target"] = local_target
    payload["tags"] = tags
    return payload
