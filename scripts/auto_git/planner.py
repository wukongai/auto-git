"""创建和校验不可变操作计划。"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .git_facts import inspect_repo
from .runner import run
from .schema import SCHEMA_VERSION, hash_payload


SUPPORTED_ACTIONS = {
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


class PlanError(RuntimeError):
    pass


_ACTION_CONTRACT = {
    "init": (
        "初始化 Git 仓库",
        "medium",
        ["目标目录成为 Git 仓库"],
        "保留用户文件；初始化失败不删除目录",
    ),
    "configure_identity": (
        "配置当前仓库 Git 身份",
        "medium",
        ["local user.name/user.email 与批准值一致"],
        "根据 operation record 恢复原 local 配置",
    ),
    "stage_commit": (
        "精确暂存并创建 Commit",
        "medium",
        ["Commit 仅包含批准路径", "HEAD 等于记录 OID"],
        "恢复 Auto Git 拥有且未漂移的 index 备份",
    ),
    "remote_connect": (
        "连接一个 Git Remote",
        "medium",
        ["Remote 名称与脱敏仓库身份一致"],
        "只对本 operation 新增且未漂移的 Remote 提供恢复建议",
    ),
    "push": (
        "Push 一个明确分支",
        "high",
        ["远端分支 OID 等于批准的本地 HEAD", "upstream 已验证"],
        "公开历史不自动回滚；失败后重读远端事实",
    ),
    "tag": (
        "创建 annotated Tag",
        "high",
        ["Tag 类型为 annotated 且 target 等于批准 OID"],
        "仅在 Tag 未公开且身份未漂移时重新计划删除",
    ),
    "push_tag": (
        "Push 单个 annotated Tag",
        "high",
        ["远端 Tag object/target 与本地完全一致"],
        "公开 Tag 不自动删除或覆盖",
    ),
    "github_repo_create": (
        "创建 GitHub 仓库（不 Push）",
        "high",
        ["Owner/name/visibility 与批准值一致", "未隐式 Push"],
        "外部仓库不自动删除",
    ),
    "github_release": (
        "创建 GitHub Release",
        "high",
        ["Release Tag、target、状态和 assets 与批准值一致"],
        "公开 Release 不自动删除或覆盖",
    ),
    "recover_index": (
        "恢复 Auto Git 拥有的 index 备份",
        "high",
        ["index checksum 等于受管备份", "已创建 undo backup"],
        "使用本次恢复前创建的 undo backup 重新计划恢复",
    ),
}


def _required_string(params: dict[str, Any], key: str) -> str:
    value = params.get(key)
    if not isinstance(value, str) or not value:
        raise PlanError(f"{key} 必须是非空字符串")
    return value


def _validate_relative_paths(values: object, *, label: str) -> list[str]:
    if not isinstance(values, list) or not values:
        raise PlanError(f"{label} 不能为空")
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            raise PlanError(f"{label} 包含无效路径")
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise PlanError(f"{label} 只能使用项目相对路径")
        normalized.append(value)
    if len(normalized) != len(set(normalized)):
        raise PlanError(f"{label} 不能重复")
    return normalized


def _validate_commands(value: object, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        raise PlanError(f"{label} 必须是 argv 数组")
    for command in value:
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(item, str) and item for item in command)
        ):
            raise PlanError(f"{label} 必须是非空 argv 数组")


def _validate_action_params(
    action: str,
    repo: Path,
    params: dict[str, Any],
) -> dict[str, Any]:
    normalized = deepcopy(params)
    if action == "init":
        branch = normalized.get("branch", "main")
        if (
            not isinstance(branch, str)
            or branch.startswith("-")
            or run(
                ["git", "check-ref-format", "--branch", branch],
                cwd=repo,
                check=False,
            ).returncode
        ):
            raise PlanError("branch 名称无效")
        normalized["branch"] = branch
    elif action == "configure_identity":
        if normalized.get("scope", "local") != "local":
            raise PlanError("0.1.0 只允许 local identity 计划")
        _required_string(normalized, "name")
        email = _required_string(normalized, "email")
        if "@" not in email or any(char.isspace() for char in email):
            raise PlanError("email 格式无效")
        normalized["scope"] = "local"
    elif action == "stage_commit":
        normalized["paths"] = _validate_relative_paths(
            normalized.get("paths"),
            label="paths",
        )
        _required_string(normalized, "message")
        _validate_commands(normalized.get("regression", []), "regression")
    elif action == "remote_connect":
        from .remote import (
            RemoteError,
            normalize_remote_url,
            validate_remote_name,
        )

        try:
            validate_remote_name(
                repo,
                normalized.get("name", "origin"),
                require_configured=False,
            )
            normalize_remote_url(_required_string(normalized, "url"))
        except RemoteError as exc:
            raise PlanError(str(exc)) from exc
        normalized["name"] = normalized.get("name", "origin")
    elif action == "push":
        from .remote import RemoteError, _validate_branch, validate_remote_name

        try:
            validate_remote_name(
                repo,
                normalized.get("remote", "origin"),
                require_configured=True,
            )
            _validate_branch(repo, _required_string(normalized, "branch"))
        except RemoteError as exc:
            raise PlanError(str(exc)) from exc
        normalized["remote"] = normalized.get("remote", "origin")
    elif action in {"tag", "push_tag"}:
        from .release import ReleaseError, validate_tag_name

        raw_tag = (
            normalized["tag"]
            if "tag" in normalized
            else f"v{_required_string(normalized, 'version')}"
        )
        try:
            normalized["tag"] = validate_tag_name(repo, raw_tag)
        except ReleaseError as exc:
            raise PlanError(str(exc)) from exc
        if action == "push_tag":
            from .remote import RemoteError, validate_remote_name

            try:
                validate_remote_name(
                    repo,
                    normalized.get("remote", "origin"),
                    require_configured=True,
                )
            except RemoteError as exc:
                raise PlanError(str(exc)) from exc
            normalized["remote"] = normalized.get("remote", "origin")
    elif action == "github_repo_create":
        from .github import (
            GITHUB_HOSTNAME,
            GitHubError,
            auth_status,
            validate_repository_name,
        )

        try:
            validate_repository_name(_required_string(normalized, "name"))
        except GitHubError as exc:
            raise PlanError(str(exc)) from exc
        if normalized.get("visibility") not in {"public", "private", "internal"}:
            raise PlanError("visibility 必须显式为 private/public/internal")
        authentication = auth_status()
        if not authentication["authenticated"]:
            raise PlanError("GitHub 认证或账号/协议事实不完整")
        normalized["authenticated_account"] = authentication["account"]
        normalized["git_protocol"] = authentication["git_protocol"]
        normalized["hostname"] = GITHUB_HOSTNAME
    elif action == "github_release":
        _required_string(normalized, "version")
        _required_string(normalized, "remote")
        _required_string(normalized, "notes")
        _required_string(normalized, "title")
        from .remote import RemoteError, validate_remote_name
        from .release import ReleaseError, validate_tag_name

        try:
            validate_remote_name(
                repo,
                normalized["remote"],
                require_configured=True,
            )
            validate_tag_name(repo, f"v{normalized['version']}")
        except (RemoteError, ReleaseError) as exc:
            raise PlanError(str(exc)) from exc
        from .github import (
            GITHUB_HOSTNAME,
            GitHubError,
            auth_status,
            validate_repository_name,
        )

        try:
            normalized["repository"] = validate_repository_name(
                _required_string(normalized, "repository")
            )
        except GitHubError as exc:
            raise PlanError(str(exc)) from exc
        authentication = auth_status()
        if not authentication["authenticated"]:
            raise PlanError("GitHub 认证或账号/协议事实不完整")
        normalized["authenticated_account"] = authentication["account"]
        normalized["git_protocol"] = authentication["git_protocol"]
        normalized["hostname"] = GITHUB_HOSTNAME
        if not isinstance(normalized.get("draft"), bool) or not isinstance(
            normalized.get("prerelease"),
            bool,
        ):
            raise PlanError("draft/prerelease 必须是布尔值")
        assets = normalized.get("assets", [])
        if assets:
            normalized["assets"] = _validate_relative_paths(
                assets,
                label="assets",
            )
            checksums: dict[str, str] = {}
            for value in normalized["assets"]:
                asset = (repo / value).resolve()
                if not asset.is_file():
                    raise PlanError(f"Release asset 不存在：{value}")
                checksums[value] = hashlib.sha256(asset.read_bytes()).hexdigest()
            normalized["asset_checksums"] = checksums
        elif not isinstance(assets, list):
            raise PlanError("assets 必须是路径数组")
        else:
            normalized["asset_checksums"] = {}
    elif action == "recover_index":
        for key in (
            "record_path",
            "record_plan_id",
            "index_backup",
            "index_backup_checksum",
            "expected_current_index_checksum",
        ):
            _required_string(normalized, key)
    return normalized


def _hashable(plan: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(plan)
    value.pop("plan_hash", None)
    return value


def create_plan(
    action: str,
    repo: Path | str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if action not in SUPPORTED_ACTIONS:
        raise PlanError(f"不支持的 action：{action}")
    facts = inspect_repo(repo)
    if action != "init" and not facts["is_repo"]:
        raise PlanError("目标不是 Git 仓库")
    repo_path = Path(facts["path"])
    normalized_params = _validate_action_params(
        action,
        repo_path,
        params or {},
    )
    summary, risk, postconditions, rollback = _ACTION_CONTRACT[action]
    now = datetime.now(timezone.utc)
    plan = {
        "schema_version": SCHEMA_VERSION,
        "id": f"plan-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
        "action": action,
        "repo": facts["path"],
        "precondition_fingerprint": facts["fingerprint"],
        "params": normalized_params,
        "requires_approval": True,
        "summary": summary,
        "risk": risk,
        "expected_postconditions": postconditions,
        "rollback": rollback,
        "created_at": now.isoformat(),
    }
    plan["plan_hash"] = hash_payload(plan)
    return plan


def validate_plan(
    plan: dict[str, Any],
    *,
    current_repo: Path | str | None = None,
) -> None:
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise PlanError("plan schema_version 不受支持")
    if plan.get("action") not in SUPPORTED_ACTIONS:
        raise PlanError("plan action 不受支持")
    if plan.get("requires_approval") is not True:
        raise PlanError("plan 缺少动作级审批")
    if not all(
        plan.get(key)
        for key in (
            "summary",
            "risk",
            "expected_postconditions",
            "rollback",
        )
    ):
        raise PlanError("plan 审批合同不完整")
    if plan.get("plan_hash") != hash_payload(_hashable(plan)):
        raise PlanError("plan hash 不匹配")
    if current_repo is not None:
        current = inspect_repo(current_repo)
        if current["fingerprint"] != plan.get("precondition_fingerprint"):
            raise PlanError("仓库事实已漂移")
