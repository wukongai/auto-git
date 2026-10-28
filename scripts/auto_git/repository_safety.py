"""计划与锁内执行共用的只读仓库现场守门。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .runner import CommandError, run


_READ_ONLY_ACTIONS = frozenset({"inspect", "doctor", "history", "verify", "review"})
_OPERATION_MARKERS = (
    ("MERGE_HEAD", "merge"),
    ("rebase-merge", "rebase"),
    ("rebase-apply", "rebase"),
    ("CHERRY_PICK_HEAD", "cherry-pick"),
    ("REVERT_HEAD", "revert"),
    ("BISECT_LOG", "bisect"),
    ("BISECT_START", "bisect"),
    ("sequencer", "sequencer"),
)
_UNMERGED_CODES = frozenset({"DD", "AU", "UD", "UA", "DU", "AA", "UU"})


class UnsafeRepositoryError(RuntimeError):
    """当前现场不能安全进行普通写入，需要人工处理后重新预览。"""


def _git(repo: Path, *args: str):
    """仅调用只读Git查询，不获取锁或使用本地化错误作用户反馈。"""
    return run(
        ["git", *args], cwd=repo, check=False,
        env={"LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0"},
    )


def _scan_error(error: OSError) -> None:
    """目录不可读时不能把未扫描部分视为没有嵌套仓库。"""
    raise error


def _ensure_initialization_boundary(repo: Path) -> None:
    """重新探测父仓、bare仓及嵌套仓边界，不实际初始化。"""
    probe = _git(repo, "rev-parse", "--git-dir")
    if probe.returncode == 0:
        raise UnsafeRepositoryError("目标已属于 Git 仓库，请复用现有仓库并明确项目根目录")
    if "not a git repository" not in probe.stderr.lower():
        raise UnsafeRepositoryError("无法确认 Git 初始化边界，请先检查仓库现场")
    for _, directories, files in os.walk(repo, followlinks=False, onerror=_scan_error):
        if ".git" in directories or ".git" in files:
            raise UnsafeRepositoryError("目标包含嵌套 Git 仓库，请先明确项目边界后再初始化")


def _ensure_current_root(repo: Path) -> None:
    """不允许事实目录在盘点后变成别的仓库或子目录。"""
    probe = _git(repo, "rev-parse", "--show-toplevel")
    if probe.returncode or Path(probe.stdout.strip()).resolve() != repo:
        raise UnsafeRepositoryError("Git 仓库根目录不匹配，请明确实际根目录并重新预览")


def _ensure_no_operation_markers(repo: Path) -> None:
    """使用--git-path兼容worktree，不假定.git一定是目录。"""
    for marker, label in _OPERATION_MARKERS:
        probe = _git(repo, "rev-parse", "--git-path", marker)
        if probe.returncode or not probe.stdout.strip():
            raise UnsafeRepositoryError("无法读取 Git 操作现场，请检查后重新预览")
        marker_path = Path(probe.stdout.strip())
        if not marker_path.is_absolute():
            marker_path = repo / marker_path
        if marker_path.exists() or marker_path.is_symlink():
            raise UnsafeRepositoryError(
                f"Git 存在 {label} 操作现场，普通写入已停止；请人工处理后重新预览"
            )


def ensure_safe_repository(facts: dict[str, Any], action: str) -> None:
    """只读拒绝不安全写入；initial HEAD不等于detached HEAD。"""
    if action in _READ_ONLY_ACTIONS:
        return
    try:
        if not isinstance(facts, dict) or not isinstance(facts.get("path"), str):
            raise UnsafeRepositoryError("仓库路径事实不完整，请重新盘点")
        if not facts["path"] or not isinstance(facts.get("is_repo"), bool):
            raise UnsafeRepositoryError("仓库事实不完整，请重新盘点")
        repo = Path(facts["path"]).expanduser().resolve()
        if not repo.is_dir():
            raise UnsafeRepositoryError("目标目录不存在，无法确认安全现场")
        if action == "init":
            if facts["is_repo"]:
                raise UnsafeRepositoryError("目标已是 Git 仓库，请复用现有仓库，无需再次初始化")
            _ensure_initialization_boundary(repo)
            return
        if not facts["is_repo"]:
            raise UnsafeRepositoryError("目标不是 Git 仓库，请先明确初始化范围")
        if facts.get("operation"):
            raise UnsafeRepositoryError("Git 存在进行中的操作，普通写入已停止；请人工处理后重新预览")
        changes = facts.get("changes")
        if not isinstance(changes, list) or any(not isinstance(item, dict) for item in changes):
            raise UnsafeRepositoryError("工作区变化事实不完整，请重新盘点")
        if any(
            item.get("kind") == "unmerged" or item.get("xy") in _UNMERGED_CODES
            for item in changes
        ):
            raise UnsafeRepositoryError("Git 存在未合并冲突路径，请人工处理后重新预览")
        branch = facts.get("branch")
        if branch in {"(detached)", "HEAD"}:
            raise UnsafeRepositoryError("detached HEAD 不允许普通写入，请先选择明确分支")
        if not isinstance(branch, str) or not branch:
            raise UnsafeRepositoryError("分支事实不完整，请重新盘点")
        _ensure_current_root(repo)
        _ensure_no_operation_markers(repo)
        symbolic = _git(repo, "symbolic-ref", "--quiet", "HEAD")
        if symbolic.returncode:
            raise UnsafeRepositoryError("detached HEAD 或分支现场不明，请先选择明确分支")
        if symbolic.stdout.strip() != f"refs/heads/{branch}":
            raise UnsafeRepositoryError("分支现场已变化，请重新预览")
    except UnsafeRepositoryError:
        raise
    except (CommandError, OSError, TypeError, ValueError) as exc:
        raise UnsafeRepositoryError("无法核对仓库安全现场，请检查后重新预览") from exc
