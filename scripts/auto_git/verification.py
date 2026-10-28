"""按 action 重读机器事实，独立复验 Auto Git operation record。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .runner import CommandError, run


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


class VerificationUnknown(RuntimeError):
    """缺少可读取事实，不能将结果归为确定漂移。"""


class VerificationPartial(RuntimeError):
    """目标已收到，但本地跟踪等完整后置条件尚未满足。"""


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
        from .commit_execution import verify_commit
        return verify_commit(repo, details)
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
        if details.get("object") is None and details.get("existed_before") is False:
            return bool(facts.get("exists")) and facts.get("target") == details.get("target")
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
        from .remote import normalize_remote_url, validate_remote_name

        remote = validate_remote_name(
            repo,
            details.get("name", ""),
            require_configured=True,
        )
        branch = details.get("branch", "")
        endpoint = remote
        if details.get("url_identity"):
            endpoint = run(["git", "remote", "get-url", "--push", "--", remote], cwd=repo).stdout.strip()
            if normalize_remote_url(endpoint) != details["url_identity"]:
                return False
        result = run(
            ["git", "ls-remote", endpoint, f"refs/heads/{branch}"],
            cwd=repo,
            check=False,
        )
        if result.returncode:
            raise VerificationUnknown("无法读取远端，结果未知；先恢复读取再核验")
        oid = result.stdout.split()[0] if result.stdout.split() else ""
        if not details.get("remote") or oid != details["remote"]:
            return False
        local = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
        if local != details.get("local", details["remote"]):
            return False
        upstream = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], cwd=repo, check=False).stdout.strip()
        if upstream != f"{remote}/{branch}":
            raise VerificationPartial("远端已收到批准提交，但本地upstream未匹配；先单独确认跟踪配置")
        return True
    from .release import _remote_tag_facts
    from .remote import normalize_remote_url

    remote_name = details.get("remote", "")
    endpoint = None
    if details.get("url_identity"):
        endpoint = run(["git", "remote", "get-url", "--push", "--", remote_name], cwd=repo).stdout.strip()
        if normalize_remote_url(endpoint) != details["url_identity"]:
            return False
    else:
        raise VerificationUnknown("旧Tag记录缺少原目标身份，请结合原计划先确认目标后核验")

    facts = _remote_tag_facts(
        repo,
        remote_name,
        details.get("tag", ""),
        endpoint=endpoint,
    )
    return (
        facts.get("object") == details.get("object")
        and facts.get("target") == details.get("target")
    )


def _verify_github_repo(repo: Path, details: dict[str, Any]) -> bool:
    from .github import GITHUB_HOSTNAME, github_env, validate_repository_name

    repository = validate_repository_name(details.get("name", ""))
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
    from .github import GITHUB_HOSTNAME, github_env, validate_repository_name
    from .release import (
        _github_tag_facts,
        _local_tag_facts,
        _release_asset_digests,
        _remote_tag_facts,
    )

    repository = validate_repository_name(details.get("repository", ""))
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
    body = facts.get("body")
    notes_match = (
        isinstance(body, str) and hashlib.sha256(body.encode("utf-8")).hexdigest() == details["notes_sha256"]
        if details.get("notes_sha256") else body == details.get("notes")
    )
    actual_url = facts.get("url")
    url_match = (
        actual_url == details["url"] if details.get("url") else
        isinstance(actual_url, str) and actual_url.startswith(f"https://github.com/{repository}/releases/")
    )
    provider_target = details.get("provider_target")
    target_match = (
        facts.get("targetCommitish") == provider_target if provider_target is not None else
        facts.get("targetCommitish") in {details.get("target"), details.get("expected_branch")}
    )
    return (
        local_tag.get("object") == details.get("tag_object")
        and local_tag.get("target") == details.get("target")
        and remote_tag.get("object") == details.get("tag_object")
        and remote_tag.get("target") == details.get("target")
        and provider_tag.get("object") == details.get("provider_tag_object")
        and provider_tag.get("target") == details.get("provider_tag_target")
        and facts.get("tagName") == details.get("tag")
        and facts.get("name") == details.get("title")
        and notes_match
        and facts.get("isDraft") is details.get("draft")
        and facts.get("isPrerelease") is details.get("prerelease")
        and target_match
        and url_match
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
    except VerificationPartial as exc:
        return {
            "schema_version": "1", "record_plan_id": safe_record.get("plan_id"),
            "verified": False, "verification_status": "partial", "action": action,
            "remote_applied": True, "reason": str(exc),
            "next_step": "保留远端成果；单独预览本地upstream配置，不重复推送",
        }
    except VerificationUnknown as exc:
        return {
            "schema_version": "1", "record_plan_id": safe_record.get("plan_id"),
            "verified": None, "verification_status": "unknown", "action": action,
            "reason": str(exc), "next_step": "恢复网络后只读核对目标远端，不要盲目重试写入",
        }
    except (
        RuntimeError,
        OSError,
        ValueError,
        KeyError,
        AttributeError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        if action in {"push", "push_tag", "github_repo_create", "github_release"} and (
            isinstance(exc, CommandError) or getattr(exc, "verification_unavailable", False)
        ):
            return {
                "schema_version": "1", "record_plan_id": safe_record.get("plan_id"),
                "verified": None, "verification_status": "unknown", "action": action,
                "reason": "目标状态暂时无法读取，不能断言成功或漂移",
                "next_step": "恢复读取能力后重新只读核验，不盲目重试写入",
            }
        verified = False
    return {
        "schema_version": "1",
        "record_plan_id": safe_record.get("plan_id"),
        "verified": verified,
        "verification_status": "verified" if verified else "drifted",
        "action": action,
    }
