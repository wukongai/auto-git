"""精确暂存、真实检查及不改写已产生历史的 Commit 核验。"""

from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path
from typing import Any

from .git_facts import _update_path_digest, inspect_repo
from .recovery import _atomic_replace_from, _git_dir, _index_checksum
from .regression import RegressionError, run_regression
from .runner import run
from .schema import hash_payload
from .sensitive_paths import is_sensitive_path


DOCUMENT_SUFFIXES = {".md", ".txt", ".rst", ".adoc"}
INTEGRITY_COMMAND = ["git", "diff", "--cached", "--check"]


class CommitSafetyError(RuntimeError):
    """向主执行器传递失败事实，禁止把已发生 Commit 当作未执行。"""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None,
                 commit_created: bool = False):
        super().__init__(message)
        self.details = details or {}
        self.commit_created = commit_created


def _git(repo: Path, *args: str, check: bool = True) -> str:
    """只用 argv 执行 Git，路径始终按 literal 解释。"""
    return run(["git", *args], cwd=repo, check=check,
               env={"GIT_LITERAL_PATHSPECS": "1"}).stdout.strip("\n")


def _head(repo: Path) -> str | None:
    """合法未出生 HEAD 返回 None。"""
    result = run(["git", "rev-parse", "--verify", "HEAD"], cwd=repo, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _visible_paths(repo: Path) -> list[str]:
    """只列 Git 可见路径，不读取任何正文。"""
    names = _git(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted(set(names.split("\0")) - {""})


def _require_safe_paths(paths: list[str]) -> None:
    """发现敏感路径只报告路径，不进入正文摘要或暂存。"""
    sensitive = sorted({name for name in paths if is_sensitive_path(name)})
    if sensitive:
        raise CommitSafetyError("检测到敏感路径，停止读取或暂存：" + ", ".join(sensitive),
                                details={"sensitive_paths": sensitive})


def _visible_workspace(repo: Path) -> dict[str, str]:
    """保存可见非敏感路径摘要；忽略路径不读取，示例名字不证明无凭证。"""
    names = _visible_paths(repo)
    _require_safe_paths(names)
    snapshot: dict[str, str] = {}
    for name in names:
        digest = hashlib.sha256()
        _update_path_digest(digest, repo, name)
        snapshot[name] = digest.hexdigest()
    return snapshot


def _actual_commit(repo: Path, base_head: str | None) -> dict[str, Any]:
    """独立回读真实 Commit 树、父提交及相对原 HEAD 的完整路径。"""
    head = _head(repo)
    if not head:
        raise CommitSafetyError("没有可核验的 Commit")
    arguments = (["diff", "--name-only", "--no-renames", "-z", base_head, head]
                 if base_head else
                 ["diff-tree", "--root", "--no-commit-id", "--name-only", "--no-renames", "-r", "-z", head])
    return {
        "head": head,
        "actual_tree": _git(repo, "rev-parse", f"{head}^{{tree}}"),
        "actual_parents": _git(repo, "show", "-s", "--format=%P", head).split(),
        "actual_paths": sorted(set(_git(repo, *arguments).split("\0")) - {""}),
    }


def _check_paths(paths: object) -> list[str]:
    """防止专用接口绕过相对路径和精确文件集合约束。"""
    if not isinstance(paths, list) or not paths or any(
        not isinstance(item, str) or not item or "\0" in item
        or Path(item).is_absolute() or ".." in Path(item).parts for item in paths
    ):
        raise CommitSafetyError("精确 staging 只能使用非空项目相对路径")
    if len(paths) != len(set(paths)):
        raise CommitSafetyError("精确 staging 路径不能重复")
    return sorted(paths)


def _backup_index(repo: Path, plan: dict[str, Any], home: Path) -> dict[str, Any]:
    """保留原 index，兼容既有受管恢复合同。"""
    index = _git_dir(repo) / "index"
    backup = home / "index-backups" / f"{plan['id']}.index"
    if not index.is_file():
        return {"index_backup": None, "index_backup_checksum": None}
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(index, backup)
    checksum = hashlib.sha256(backup.read_bytes()).hexdigest()
    backup.with_suffix(".index.sha256").write_text(checksum + "\n", encoding="ascii")
    return {"index_backup": str(backup), "index_backup_checksum": checksum}


def _checks(repo: Path, commands: list, details: dict[str, Any]) -> None:
    """检查已暂存的真实内容，并将成功或失败的 argv/退出码留在回执。"""
    results = details["checks"]["results"]
    try:
        results.extend(run_regression([INTEGRITY_COMMAND], repo))
        if commands:
            results.extend(run_regression(commands, repo))
    except RegressionError as exc:
        results.extend(exc.results)
        details["checks"]["status"] = "failed"
        raise
    details["checks"]["status"] = "succeeded"


def _capture_postflight(repo: Path, details: dict[str, Any], before: dict[str, str]) -> None:
    """记录 Commit、完成时 index 及工作区事实，不修改 hook 留下的现场。"""
    evidence = details["commit_evidence"]
    actual = _actual_commit(repo, evidence["base_head"])
    details["head"] = actual.pop("head")
    evidence.update(actual)
    evidence["post_index_tree"] = _git(repo, "write-tree")
    evidence["post_index_matches_commit"] = (
        evidence["post_index_tree"] == evidence["staged_tree"] == evidence["actual_tree"]
    )
    evidence["index_verification_scope"] = "captured_post_commit"
    after = _visible_workspace(repo)
    evidence["workspace_changes"] = sorted(
        name for name in before.keys() | after.keys() if before.get(name) != after.get(name)
    )
    evidence["workspace_changed"] = bool(evidence["workspace_changes"])
    evidence["post_workspace_fingerprint"] = hash_payload(after)


def _restore_owned_index(repo: Path, details: dict[str, Any], owned_checksum: str | None) -> None:
    """仅恢复仍与本模块最后拥有状态相等的 index，保留 hook 改动。"""
    details["index_restored"] = False
    backup = details.get("index_backup")
    if backup and owned_checksum and _index_checksum(repo) == owned_checksum:
        _atomic_replace_from(Path(backup), _git_dir(repo) / "index")
        details["index_restored"] = True


def execute_commit(repo: Path, plan: dict[str, Any], state_home: Path) -> dict[str, Any]:
    """执行已批准的 Commit；失败携带事实，永不 reset 已产生的提交。"""
    params = plan["params"]
    base_head = _head(repo)
    commands = params.get("regression", [])
    details: dict[str, Any] = {
        "paths": [], "head": base_head, "index_backup": None,
        "index_backup_checksum": None,
        "checks": {"profile": "project" if commands else "integrity", "results": [],
                   "status": "not_started", "business_correctness_proven": False},
        "commit_evidence": {"base_head": base_head},
    }
    owned_checksum = None
    workspace: dict[str, str] | None = None
    try:
        paths = _check_paths(params.get("paths"))
        details["paths"] = paths
        _require_safe_paths(paths + _visible_paths(repo))
        if not commands and any(Path(item).suffix.lower() not in DOCUMENT_SUFFIXES for item in paths):
            raise CommitSafetyError("代码或配置提交缺少显式项目回归命令，拒绝空过门禁")
        for key in ("user.name", "user.email"):
            if not _git(repo, "config", "--get", key, check=False).strip():
                raise CommitSafetyError("Git identity 缺失")
        details.update(_backup_index(repo, plan, state_home))
        run(["git", "add", "--pathspec-from-file=-", "--pathspec-file-nul"], cwd=repo,
            env={"GIT_LITERAL_PATHSPECS": "1"},
            input_bytes=b"\0".join(item.encode("utf-8") for item in paths) + b"\0")
        staged = sorted(set(_git(repo, "diff", "--cached", "--name-only", "--no-renames", "-z").split("\0")) - {""})
        details["commit_evidence"]["staged_tree"] = _git(repo, "write-tree")
        staged_fingerprint = inspect_repo(repo)["fingerprint"]
        owned_checksum = _index_checksum(repo)
        if staged != paths:
            raise CommitSafetyError("staging 范围与审批不一致")
        workspace = _visible_workspace(repo)
        _checks(repo, commands, details)
        _require_safe_paths(_visible_paths(repo))
        if inspect_repo(repo)["fingerprint"] != staged_fingerprint:
            raise CommitSafetyError("检查后仓库事实漂移，保留检查副作用并阻断 Commit")
        owned_checksum = _index_checksum(repo)
        _git(repo, "commit", "-m", params["message"], "--")
        _capture_postflight(repo, details, workspace)
        details["post_index_checksum"] = _index_checksum(repo)
        details["status"] = "succeeded"
        if not verify_commit(repo, details):
            raise CommitSafetyError("Commit 已产生，但真实提交范围、内容、父提交、暂存区或工作区核验失败")
        return details
    except Exception as exc:
        if isinstance(exc, CommitSafetyError):
            details.update(exc.details)
        created = _head(repo) is not None and _head(repo) != base_head
        details["head"] = _head(repo)
        details["status"] = "verification_failed" if created else "failed"
        details["safe_next_step"] = "保留当前提交与文件，重新 inspect 并核对差异；不要 reset 或盲目重试"
        try:
            if created and workspace is not None:
                _capture_postflight(repo, details, workspace)
            elif not created:
                _restore_owned_index(repo, details, owned_checksum)
            details["post_index_checksum"] = _index_checksum(repo)
        except (OSError, RuntimeError) as recovery_error:
            details["preservation_error"] = type(recovery_error).__name__
        raise CommitSafetyError(str(exc), details=details, commit_created=created) from exc


def verify_commit(repo: Path, details: dict[str, Any]) -> bool:
    """重读 Commit 并认证完成时 index 证据，不声称后续暂存区仍无变化。"""
    try:
        evidence = details["commit_evidence"]
        required = {"base_head", "staged_tree", "actual_tree", "actual_paths",
                    "actual_parents", "workspace_changed", "post_index_tree",
                    "post_index_matches_commit", "index_verification_scope"}
        if not required <= evidence.keys() or details.get("status") != "succeeded":
            return False
        if evidence["base_head"] is not None and not re.fullmatch(
            r"(?:[0-9a-f]{40}|[0-9a-f]{64})", str(evidence["base_head"])
        ):
            return False
        actual = _actual_commit(repo, evidence["base_head"])
        parents = [evidence["base_head"]] if evidence["base_head"] else []
        results = details["checks"]["results"]
        return bool(results) and all(item["returncode"] == 0 for item in results) and (
            actual["head"] == details["head"]
            and actual["actual_parents"] == parents == evidence["actual_parents"]
            and actual["actual_tree"] == evidence["staged_tree"] == evidence["actual_tree"]
            and evidence["post_index_tree"] == evidence["staged_tree"]
            and evidence["post_index_matches_commit"] is True
            and evidence["index_verification_scope"] == "captured_post_commit"
            and actual["actual_paths"] == sorted(details["paths"]) == evidence["actual_paths"]
            and evidence["workspace_changed"] is False
        )
    except (KeyError, TypeError, AttributeError, OSError, RuntimeError):
        return False
