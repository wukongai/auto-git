"""应用本地初始化、身份和精确 Commit 计划。"""

from __future__ import annotations

import hashlib
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .planner import PlanError, validate_plan
from .regression import RegressionError, run_regression
from .runner import CommandError, run
from .state import (
    RepositoryLock,
    atomic_write_json,
    default_state_home,
    read_json,
)


class ApplyError(RuntimeError):
    pass


def _git_dir(repo: Path) -> Path:
    value = Path(run(["git", "rev-parse", "--git-dir"], cwd=repo).stdout.strip())
    return value if value.is_absolute() else repo / value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _identity(repo: Path) -> tuple[str, str]:
    name = run(["git", "config", "--get", "user.name"], cwd=repo, check=False)
    email = run(["git", "config", "--get", "user.email"], cwd=repo, check=False)
    return name.stdout.strip(), email.stdout.strip()


def _record_path(state_home: Path, plan: dict[str, Any]) -> Path:
    return state_home / "records" / f"{plan['id']}.json"


def apply_plan(
    plan: dict[str, Any],
    *,
    approval: str,
    state_home: Path | None = None,
) -> dict[str, Any]:
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
                raise ApplyError("已有 operation record 身份不匹配，拒绝重放")
            verification = verify_record(existing)
            if verification.get("verified") is True:
                replay = deepcopy(existing)
                replay["idempotent_replay"] = True
                return replay
            raise ApplyError("已有 operation record 的 postcondition 已漂移，拒绝重放")
        try:
            validate_plan(plan, current_repo=repo)
        except PlanError as exc:
            raise ApplyError(str(exc)) from exc
        try:
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
                )
                details["name"] = params_name
            elif action == "push":
                from .remote import push_branch

                details = push_branch(
                    repo,
                    plan["params"].get("remote", "origin"),
                    plan["params"]["branch"],
                )
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
                from .release import validate_tag_name

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
                run(["git", "push", "--", remote, f"refs/tags/{tag}"], cwd=repo)
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
                        remote,
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
        except (CommandError, RegressionError, KeyError) as exc:
            raise ApplyError(f"执行失败：{exc}") from exc
        record = {
            "schema_version": "1",
            "plan_id": plan["id"],
            "plan_hash": plan["plan_hash"],
            "repo": str(repo),
            "action": action,
            "status": "succeeded",
            "details": details,
            "owned": True,
            "index_backup": details.get("index_backup"),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        atomic_write_json(record_path, record)
        return record


def _stage_commit(repo: Path, plan: dict[str, Any], state_home: Path) -> dict[str, Any]:
    params = plan["params"]
    paths = params.get("paths") or []
    if not paths or any(not isinstance(path, str) or not path for path in paths):
        raise ApplyError("精确 staging 路径不能为空")
    if len(paths) != len(set(paths)):
        raise ApplyError("精确 staging 路径不能重复")
    name, email = _identity(repo)
    if not name or not email:
        raise ApplyError("Git identity 缺失")
    run_regression(params.get("regression", []), repo)
    try:
        validate_plan(plan, current_repo=repo)
    except PlanError as exc:
        raise ApplyError(f"回归后仓库事实漂移：{exc}") from exc
    git_dir = _git_dir(repo)
    index = git_dir / "index"
    backup = state_home / "index-backups" / f"{plan['id']}.index"
    backup.parent.mkdir(parents=True, exist_ok=True)
    if index.exists():
        shutil.copy2(index, backup)
        backup.with_suffix(f"{backup.suffix}.sha256").write_text(
            _sha256(backup) + "\n",
            encoding="ascii",
        )
    input_bytes = b"\0".join(path.encode("utf-8") for path in paths) + b"\0"
    try:
        run(
            ["git", "add", "--pathspec-from-file=-", "--pathspec-file-nul"],
            cwd=repo,
            input_bytes=input_bytes,
        )
        staged = run(["git", "diff", "--cached", "--name-only", "-z"], cwd=repo)
        staged_paths = {
            item
            for item in staged.stdout.split("\0")
            if item
        }
        if staged_paths != set(paths):
            raise ApplyError(
                f"staging 范围与审批不一致：{sorted(staged_paths)} != {sorted(paths)}"
            )
        run(["git", "commit", "-m", params["message"], "--"], cwd=repo)
    except Exception:
        if backup.exists():
            shutil.copy2(backup, index)
        raise
    head = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    post_index_checksum = _sha256(index) if index.is_file() else "missing"
    return {
        "head": head,
        "paths": sorted(paths),
        "index_backup": str(backup) if backup.exists() else None,
        "index_backup_checksum": _sha256(backup) if backup.exists() else None,
        "post_index_checksum": post_index_checksum,
    }


def verify_record(record: dict[str, Any]) -> dict[str, Any]:
    """兼容入口；具体 verifier 分离到 verification 模块。"""
    from .verification import verify_record as verify

    return verify(record)
