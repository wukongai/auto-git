"""GitHub CLI adapter；凭证由 gh 自己管理。"""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any

from .runner import CommandError, run


class GitHubError(RuntimeError):
    pass


_REPOSITORY_NAME = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.][A-Za-z0-9_.-]*$"
)
GITHUB_HOSTNAME = "github.com"


def github_env(repository: str | None = None) -> dict[str, str]:
    """覆盖 gh 的隐式目标环境，避免 GH_HOST/GH_REPO 重定向。"""
    return {
        "GH_HOST": GITHUB_HOSTNAME,
        "GH_REPO": repository or "",
    }


def validate_repository_name(name: str) -> str:
    if (
        not isinstance(name, str)
        or len(name) > 200
        or not _REPOSITORY_NAME.fullmatch(name)
        or ".." in name
    ):
        raise GitHubError("GitHub 仓库名称必须是安全的 owner/repo")
    return name


def auth_status() -> dict[str, Any]:
    """只返回认证能力状态；不回显 gh 的账号、Token 或诊断原文。"""
    try:
        result = run(
            ["gh", "auth", "status", "--hostname", GITHUB_HOSTNAME],
            check=False,
            env=github_env(),
        )
    except CommandError:
        return {
            "schema_version": "1",
            "provider": "github",
            "gh_available": False,
            "authenticated": False,
            "writes_performed": False,
        }
    if result.returncode:
        return {
            "schema_version": "1",
            "provider": "github",
            "gh_available": True,
            "authenticated": False,
            "account": None,
            "git_protocol": None,
            "writes_performed": False,
        }
    try:
        account = run(
            ["gh", "api", "user", "--hostname", GITHUB_HOSTNAME, "--jq", ".login"],
            env=github_env(),
        ).stdout.strip()
        protocol = run(
            ["gh", "config", "get", "git_protocol", "--host", GITHUB_HOSTNAME],
            env=github_env(),
        ).stdout.strip()
    except CommandError:
        account = ""
        protocol = ""
    authenticated = bool(account) and protocol in {"https", "ssh"}
    return {
        "schema_version": "1",
        "provider": "github",
        "gh_available": True,
        "authenticated": authenticated,
        "account": account or None,
        "git_protocol": protocol or None,
        "writes_performed": False,
    }


def create_repository(
    repo: Path,
    name: str,
    *,
    visibility: str,
    expected_account: str | None = None,
    expected_protocol: str | None = None,
) -> dict[str, Any]:
    if visibility not in {"private", "public", "internal"}:
        raise GitHubError("visibility 必须显式为 private/public/internal")
    name = validate_repository_name(name)
    authentication = auth_status()
    if not authentication["authenticated"]:
        raise GitHubError("GitHub 认证或账号/协议事实不完整")
    if (
        expected_account is not None
        and authentication["account"] != expected_account
    ) or (
        expected_protocol is not None
        and authentication["git_protocol"] != expected_protocol
    ):
        raise GitHubError("GitHub 认证账号或协议已从计划事实漂移")
    try:
        run(
            [
                "gh",
                "repo",
                "create",
                name,
                f"--{visibility}",
                "--source",
                str(repo),
            ],
            cwd=repo,
            env=github_env(name),
        )
        viewed = run(
            [
                "gh",
                "repo",
                "view",
                name,
                "--json",
                "nameWithOwner,visibility,url",
            ],
            cwd=repo,
            env=github_env(name),
        )
        facts = json.loads(viewed.stdout)
    except (CommandError, json.JSONDecodeError) as exc:
        raise GitHubError("GitHub 仓库创建失败") from exc
    actual_visibility = str(facts.get("visibility", "")).lower()
    url = facts.get("url")
    if (
        facts.get("nameWithOwner") != name
        or actual_visibility != visibility
        or not isinstance(url, str)
        or url != f"https://github.com/{name}"
    ):
        raise GitHubError("GitHub 仓库创建 postflight 不一致")
    return {
        "name": name,
        "hostname": GITHUB_HOSTNAME,
        "visibility": visibility,
        "url_identity": url,
        "authenticated_account": authentication["account"],
        "git_protocol": authentication["git_protocol"],
        "verified": True,
        "pushed": False,
    }
