"""最终审阅锁定原Tag目标与完整待公开历史的敏感路径边界。"""

from pathlib import Path
import subprocess

import pytest

from conftest import git
from auto_git.executor import apply_plan, verify_record
from auto_git.planner import create_plan


def bare(tmp_path: Path, name: str) -> Path:
    """建立纯本地远端，测试不访问真实服务。"""
    path = tmp_path / name
    subprocess.run(["git", "init", "--bare", str(path)], check=True, capture_output=True)
    return path


def test_tag_record_never_certifies_a_retargeted_remote(repo: Path, tmp_path: Path) -> None:
    """另一仓库即使有相同Tag对象，也不是本次批准目标。"""
    first, second = bare(tmp_path, "first.git"), bare(tmp_path, "second.git")
    git(repo, "remote", "add", "origin", str(first))
    git(repo, "tag", "-a", "v-fixture", "-m", "fixture")
    git(repo, "push", str(second), "refs/tags/v-fixture")
    plan = create_plan("push_tag", repo, {"remote": "origin", "tag": "v-fixture"})
    record = apply_plan(plan, approval=plan["plan_hash"], state_home=tmp_path / "state")
    assert verify_record(record)["verified"] is True
    git(repo, "remote", "set-url", "origin", str(second))
    assert verify_record(record)["verified"] is False


def test_push_blocks_sensitive_path_even_deleted_from_current_tree(repo: Path, tmp_path: Path) -> None:
    """不能只检查当前工作区；历史中的凭证路径也不得公开。"""
    remote = bare(tmp_path, "remote.git")
    git(repo, "remote", "add", "origin", str(remote))
    fixture = repo / ".env"
    fixture.write_text("not-a-real-secret\n")
    git(repo, "add", "--", ".env")
    git(repo, "commit", "-m", "test: 敏感路径夹具")
    fixture.unlink()
    git(repo, "add", "--", ".env")
    git(repo, "commit", "-m", "test: 当前树中删除夹具")
    plan = create_plan("push", repo, {"remote": "origin", "branch": "main", "regression": [["git", "status", "--short"]]})
    with pytest.raises(RuntimeError, match="敏感|凭证"):
        apply_plan(plan, approval=plan["plan_hash"], state_home=tmp_path / "state")
    assert not git(remote, "for-each-ref", "refs/heads/main")
