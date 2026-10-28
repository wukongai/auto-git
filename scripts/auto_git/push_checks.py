"""在公开已批准提交之前执行真实检查并保留结果。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .commit_execution import DOCUMENT_SUFFIXES
from .git_facts import inspect_repo
from .regression import RegressionError, run_regression
from .runner import run
from .sensitive_paths import is_sensitive_path


class PushCheckError(RegressionError):
    """检查失败发生在远程写入前，记录不能误称已经推送。"""

    before_remote_write = True

    def __init__(self, message: str, checks: dict[str, Any]):
        super().__init__(message)
        self.details = {"checks": checks}


def run_push_checks(repo: Path, snapshot: dict[str, Any], commands: list) -> dict[str, Any]:
    """逐个核对将公开的Commit，非文档内容必须有项目回归。"""
    commits = snapshot["commits"]
    checks: dict[str, Any] = {
        "profile": "project" if commands else "integrity", "results": [],
        "status": "not_started", "business_correctness_proven": False,
    }
    if not commits:
        checks.update(status="not_applicable", reason="两端已对应，没有待公开提交")
        return checks
    before = inspect_repo(repo)["fingerprint"]
    try:
        paths = set()
        for commit in commits:
            listed = run(["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "--no-renames", "-r", "-m", "-z", commit], cwd=repo)
            paths.update(value for value in listed.stdout.split("\0") if value)
        if any(is_sensitive_path(path) for path in paths):
            raise RegressionError("待公开历史包含凭证形态敏感路径，先停止并人工核对，不读取正文")
        if not commands and any(Path(path).suffix.lower() not in DOCUMENT_SUFFIXES for path in paths):
            raise RegressionError("待推送代码或配置缺少显式项目回归检查")
        integrity = [["git", "show", "--check", "--format=", commit] for commit in commits]
        checks["results"].extend(run_regression(integrity, repo))
        if commands:
            checks["results"].extend(run_regression(commands, repo))
        if inspect_repo(repo)["fingerprint"] != before:
            raise RegressionError("Push检查后仓库事实漂移，拒绝公开")
    except RegressionError as exc:
        checks["results"].extend(getattr(exc, "results", []))
        checks["status"] = "failed"
        raise PushCheckError(str(exc), checks) from exc
    checks["status"] = "succeeded"
    return checks
