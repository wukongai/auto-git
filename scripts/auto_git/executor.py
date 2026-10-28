"""应用本地初始化、身份和精确 Commit 计划。"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any

from .commit_execution import CommitSafetyError, execute_commit
from .operation_journal import OperationJournal
from .planner import PlanError, validate_plan
from .regression import RegressionError
from .runner import CommandError, run
from .state import (
    RepositoryLock,
    default_state_home,
    read_json,
)


class ApplyError(RuntimeError):
    pass


def _record_path(state_home: Path, plan: dict[str, Any]) -> Path:
    return state_home / "records" / f"{plan['id']}.json"


def apply_plan(
    plan: dict[str, Any],
    *,
    approval: str,
    state_home: Path | None = None,
) -> dict[str, Any]:
    """校验批准和锁内现场，并记录每个已开始动作的终态。"""
    if approval != plan.get("plan_hash"):
        raise ApplyError("审批值必须等于已展示的 plan hash")
    try:
        validate_plan(plan)
    except PlanError as exc:
        raise ApplyError(str(exc)) from exc
    repo = Path(str(plan["repo"]))
    home = state_home or default_state_home()
    lock = home / "locks" / f"{hashlib.sha256(str(repo).encode()).hexdigest()}.lock"
    action = str(plan["action"])
    with RepositoryLock(lock, action=action, repo=repo):
        record_path = _record_path(home, plan)
        if record_path.is_file():
            try:
                existing = read_json(record_path)
            except (OSError, ValueError) as exc:
                raise ApplyError("已有 operation record 无法读取，拒绝重放") from exc
            if (
                not isinstance(existing, dict)
                or existing.get("plan_id") != plan["id"]
                or existing.get("plan_hash") != plan["plan_hash"]
                or existing.get("repo") != str(repo)
                or existing.get("action") != action
                or existing.get("status") != "succeeded"
            ):
                raise ApplyError("已有记录未确认成功，先只读核验，拒绝盲目重放")
            if verify_record(existing).get("verified") is True:
                replay = deepcopy(existing)
                replay["idempotent_replay"] = True
                return replay
            raise ApplyError("已有 operation record 的 postcondition 已漂移，拒绝重放")
        try:
            validate_plan(plan, current_repo=repo)
        except PlanError as exc:
            raise ApplyError(str(exc)) from exc
        journal = OperationJournal(plan, home)
        journal.start()
        try:
            details = _execute_action(repo, plan, home)
        except Exception as exc:
            journal.failure(exc)
            if isinstance(exc, (CommandError, RegressionError, KeyError, CommitSafetyError)):
                raise ApplyError(f"执行失败：{exc}") from exc
            raise
        return journal.success(details)


def _execute_action(repo: Path, plan: dict[str, Any], home: Path) -> dict[str, Any]:
    """保留既有动作实现，仅组合独立的执行与核验边界。"""
    action = str(plan["action"])
    if action == "init":
        branch = plan["params"].get("branch", "main")
        run(["git", "init", "-b", branch], cwd=repo)
        details: dict[str, Any] = {"initialized": True, "branch": branch}
    elif action == "configure_identity":
        scope = plan["params"].get("scope", "local")
        if scope != "local":
            raise ApplyError("0.1.0 自动执行只允许 local identity")
        run(["git", "config", "--local", "user.name", plan["params"]["name"]], cwd=repo)
        run(["git", "config", "--local", "user.email", plan["params"]["email"]], cwd=repo)
        details = {
            "scope": "local",
            "name": plan["params"]["name"],
            "email_hash": hashlib.sha256(
                plan["params"]["email"].encode("utf-8")
            ).hexdigest(),
        }
    elif action == "stage_commit":
        details = _stage_commit(repo, plan, home)
    elif action == "remote_connect":
        from .remote import connect_remote

        details = connect_remote(
            repo,
            params_name := plan["params"].get("name", "origin"),
            plan["params"]["url"],
            expected=plan["params"]["remote_preflight"],
        )
        details["name"] = params_name
    elif action == "push":
        from .remote import push_branch
        from .push_checks import run_push_checks

        checks = run_push_checks(
            repo, plan["params"]["remote_preflight"],
            plan["params"].get("regression", []),
        )

        details = push_branch(
            repo,
            plan["params"].get("remote", "origin"),
            plan["params"]["branch"],
            expected=plan["params"]["remote_preflight"],
        )
        details["checks"] = checks
        details["url_identity"] = plan["params"]["remote_preflight"]["url_identity"]
    elif action == "tag":
        from .release import validate_tag_name

        raw_tag = (
            plan["params"]["tag"]
            if "tag" in plan["params"]
            else f"v{plan['params']['version']}"
        )
        tag = validate_tag_name(repo, raw_tag)
        if run(
            ["git", "show-ref", "--verify", f"refs/tags/{tag}"],
            cwd=repo,
            check=False,
        ).returncode == 0:
            raise ApplyError(f"Tag {tag} 已存在")
        run(
            [
                "git",
                "tag",
                "-a",
                "-m",
                plan["params"].get("message", tag),
                "--",
                tag,
            ],
            cwd=repo,
        )
        details = {
            "tag": tag,
            "object": run(
                ["git", "rev-parse", f"refs/tags/{tag}"],
                cwd=repo,
            ).stdout.strip(),
            "target": run(
                ["git", "rev-parse", f"refs/tags/{tag}^{{}}"],
                cwd=repo,
            ).stdout.strip(),
        }
    elif action == "push_tag":
        from .remote import validate_remote_name
        from .remote import normalize_remote_url
        from .remote_preflight import _urls
        from .release import _local_tag_facts, validate_tag_name

        remote = validate_remote_name(
            repo,
            plan["params"].get("remote", "origin"),
            require_configured=True,
        )
        raw_tag = (
            plan["params"]["tag"]
            if "tag" in plan["params"]
            else f"v{plan['params']['version']}"
        )
        tag = validate_tag_name(repo, raw_tag)
        endpoint = _urls(repo, remote)[1]
        local_facts = _local_tag_facts(repo, tag)
        if not local_facts.get("exists"):
            raise ApplyError("批准的annotated Tag不存在")
        run(["git", "push", "--", endpoint, f"{local_facts['object']}:refs/tags/{tag}"], cwd=repo)
        local_object = run(
            ["git", "rev-parse", f"refs/tags/{tag}"],
            cwd=repo,
        ).stdout.strip()
        local_target = run(
            ["git", "rev-parse", f"refs/tags/{tag}^{{}}"],
            cwd=repo,
        ).stdout.strip()
        remote_lines = run(
            [
                "git",
                "ls-remote",
                "--tags",
                endpoint,
                f"refs/tags/{tag}",
                f"refs/tags/{tag}^{{}}",
            ],
            cwd=repo,
        ).stdout
        remote_refs = {
            fields[1]: fields[0]
            for line in remote_lines.splitlines()
            if len(fields := line.split(maxsplit=1)) == 2
        }
        if (
            remote_refs.get(f"refs/tags/{tag}") != local_object
            or remote_refs.get(f"refs/tags/{tag}^{{}}") != local_target
        ):
            raise ApplyError("Tag Push postflight 不一致")
        details = {
            "remote": remote,
            "tag": tag,
            "verified": True,
            "object": local_object,
            "target": local_target,
            "url_identity": normalize_remote_url(endpoint),
        }
    elif action == "github_repo_create":
        from .github import create_repository

        details = create_repository(
            repo,
            plan["params"]["name"],
            visibility=plan["params"]["visibility"],
            expected_account=plan["params"]["authenticated_account"],
            expected_protocol=plan["params"]["git_protocol"],
        )
    elif action == "github_release":
        from .release import create_github_release

        release_params = plan["params"]
        details = create_github_release(
            repo,
            release_params["version"],
            repository=release_params["repository"],
            remote=release_params["remote"],
            notes=release_params["notes"],
            title=release_params["title"],
            draft=release_params["draft"],
            prerelease=release_params["prerelease"],
            assets=release_params.get("assets", []),
            asset_checksums=release_params.get("asset_checksums", {}),
            expected_account=release_params["authenticated_account"],
            expected_protocol=release_params["git_protocol"],
        )
    elif action == "recover_index":
        from .recovery import restore_index

        details = restore_index(
            repo,
            plan["params"],
            state_home=home,
            recovery_plan_id=plan["id"],
        )
    else:
        raise ApplyError(f"action {action} 应由专用 adapter 执行")
    return details


def _stage_commit(repo: Path, plan: dict[str, Any], state_home: Path) -> dict[str, Any]:
    """兼容入口，提交安全由专用模块负责。"""
    return execute_commit(repo, plan, state_home)


def verify_record(record: dict[str, Any]) -> dict[str, Any]:
    """兼容入口，按动作独立回读真实事实。"""
    from .verification import verify_record as verify
    return verify(record)
