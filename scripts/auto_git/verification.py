"""按 action 重读机器事实，独立复验 Auto Git operation record。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .runner import run


SUPPORTED_VERIFIERS = {
    "init",
    "configure_identity",
    "stage_commit",
    "remote_connect",
    "push",
    "tag",
    "push_tag",
    "github_repo_create",
    "github_release",
    "recover_index",
}


def _verify_git_local(
    repo: Path,
    action: str,
    details: dict[str, Any],
) -> bool:
    if action == "init":
        facts = run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo,
            check=False,
        )
        branch = run(
            ["git", "branch", "--show-current"],
            cwd=repo,
            check=False,
        ).stdout.strip()
        return (
            facts.returncode == 0
            and facts.stdout.strip() == "true"
            and branch == details.get("branch")
        )
    if action == "configure_identity":
        name = run(
            ["git", "config", "--local", "--get", "user.name"],
            cwd=repo,
            check=False,
        ).stdout.strip()
        email = run(
            ["git", "config", "--local", "--get", "user.email"],
            cwd=repo,
            check=False,
        ).stdout.strip()
        return name == details.get("name") and hashlib.sha256(
            email.encode("utf-8")
        ).hexdigest() == details.get("email_hash")
    if action == "stage_commit":
        actual = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
        return actual == details.get("head")
    if action == "remote_connect":
        from .remote import normalize_remote_url

        actual = run(
            ["git", "remote", "get-url", "--", details.get("name", "origin")],
            cwd=repo,
            check=False,
        ).stdout.strip()
        return bool(actual) and normalize_remote_url(actual) == details.get(
            "url_identity"
        )
    if action == "tag":
        from .release import _local_tag_facts

        facts = _local_tag_facts(repo, details.get("tag", ""))
        return (
            facts.get("object") == details.get("object")
            and facts.get("target") == details.get("target")
        )
    from .recovery import _index_checksum

    return _index_checksum(repo) == details.get("restored_index_checksum")


def _verify_remote(
    repo: Path,
    action: str,
    details: dict[str, Any],
) -> bool:
    if action == "push":
        from .remote import validate_remote_name

        remote = validate_remote_name(
            repo,
            details.get("name", ""),
            require_configured=True,
        )
        branch = details.get("branch", "")
        result = run(
            ["git", "ls-remote", remote, f"refs/heads/{branch}"],
            cwd=repo,
            check=False,
        )
        oid = result.stdout.split()[0] if result.stdout.split() else ""
        return result.returncode == 0 and oid == details.get("remote")
    from .release import _remote_tag_facts

    facts = _remote_tag_facts(
        repo,
        details.get("remote", ""),
        details.get("tag", ""),
    )
    return (
        facts.get("object") == details.get("object")
        and facts.get("target") == details.get("target")
    )


def _verify_github_repo(repo: Path, details: dict[str, Any]) -> bool:
    from .github import GITHUB_HOSTNAME, github_env

    repository = details.get("name", "")
    viewed = run(
        [
            "gh",
            "repo",
            "view",
            repository,
            "--json",
            "nameWithOwner,visibility,url",
        ],
        cwd=repo,
        env=github_env(repository),
    )
    facts = json.loads(viewed.stdout)
    return (
        facts.get("nameWithOwner") == details.get("name")
        and str(facts.get("visibility", "")).lower() == details.get("visibility")
        and facts.get("url") == details.get("url_identity")
        and details.get("hostname") == GITHUB_HOSTNAME
    )


def _verify_github_release(repo: Path, details: dict[str, Any]) -> bool:
    if not isinstance(details.get("asset_checksums"), dict):
        return False
    from .github import GITHUB_HOSTNAME, github_env
    from .release import (
        _github_tag_facts,
        _local_tag_facts,
        _release_asset_digests,
        _remote_tag_facts,
    )

    repository = details.get("repository", "")
    local_tag = _local_tag_facts(repo, details.get("tag", ""))
    remote_tag = _remote_tag_facts(
        repo,
        details.get("remote", ""),
        details.get("tag", ""),
    )
    provider_tag = _github_tag_facts(
        repo,
        repository,
        details.get("tag", ""),
    )
    viewed = run(
        [
            "gh",
            "release",
            "view",
            details.get("tag", ""),
            "--repo",
            repository,
            "--json",
            "tagName,name,body,isDraft,isPrerelease,url,targetCommitish,assets",
        ],
        cwd=repo,
        env=github_env(repository),
    )
    facts = json.loads(viewed.stdout)
    asset_digests = _release_asset_digests(facts)
    expected_digests = {
        name: f"sha256:{checksum}"
        for name, checksum in details.get("asset_checksums", {}).items()
    }
    return (
        local_tag.get("object") == details.get("tag_object")
        and local_tag.get("target") == details.get("target")
        and remote_tag.get("object") == details.get("tag_object")
        and remote_tag.get("target") == details.get("target")
        and provider_tag.get("object") == details.get("provider_tag_object")
        and provider_tag.get("target") == details.get("provider_tag_target")
        and facts.get("tagName") == details.get("tag")
        and facts.get("name") == details.get("title")
        and facts.get("body") == details.get("notes")
        and facts.get("isDraft") is details.get("draft")
        and facts.get("isPrerelease") is details.get("prerelease")
        and facts.get("targetCommitish") == details.get("provider_target")
        and facts.get("url") == details.get("url")
        and sorted(asset_digests) == details.get("assets")
        and asset_digests == expected_digests
        and details.get("hostname") == GITHUB_HOSTNAME
    )


def verify_record(record: object) -> dict[str, Any]:
    """根据当前事实复验记录；没有 verifier 时明确返回 unknown。"""
    safe_record = record if isinstance(record, dict) else {}
    action = safe_record.get("action")
    if isinstance(action, str) and action not in SUPPORTED_VERIFIERS:
        return {
            "schema_version": "1",
            "record_plan_id": safe_record.get("plan_id"),
            "verified": None,
            "verification_status": "unknown",
            "action": action,
            "reason": "当前版本没有该 action 的机器事实 verifier",
        }
    try:
        if not isinstance(action, str):
            raise TypeError("record action 无效")
        repo_value = safe_record.get("repo")
        if not isinstance(repo_value, str) or not repo_value:
            raise TypeError("record repo 无效")
        repo = Path(repo_value)
        details = safe_record.get("details", {})
        if not isinstance(details, dict):
            raise TypeError("record details 无效")
        if action in {
            "init",
            "configure_identity",
            "stage_commit",
            "remote_connect",
            "tag",
            "recover_index",
        }:
            verified = _verify_git_local(repo, action, details)
        elif action in {"push", "push_tag"}:
            verified = _verify_remote(repo, action, details)
        elif action == "github_repo_create":
            verified = _verify_github_repo(repo, details)
        else:
            verified = _verify_github_release(repo, details)
    except (
        RuntimeError,
        OSError,
        ValueError,
        KeyError,
        AttributeError,
        TypeError,
        json.JSONDecodeError,
    ):
        verified = False
    return {
        "schema_version": "1",
        "record_plan_id": safe_record.get("plan_id"),
        "verified": verified,
        "verification_status": "verified" if verified else "drifted",
        "action": action,
    }
