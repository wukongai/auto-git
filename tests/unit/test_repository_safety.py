"""验证写入前的仓库现场守门；只使用隔离临时仓库。"""

from __future__ import annotations

import importlib
import importlib.util
import subprocess
from pathlib import Path

import pytest

from conftest import git
from auto_git.git_facts import inspect_repo


WRITE_ACTIONS = (
    "init", "configure_identity", "stage_commit", "remote_connect", "push",
    "tag", "push_tag", "github_repo_create", "github_release", "recover_index",
)


@pytest.fixture(autouse=True)
def isolated_git_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """不使用真实身份、全局配置、网络或调用者遗留的仓库覆盖。"""
    for key in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
        "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "/dev/null")
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")


@pytest.fixture
def safety():
    """模块缺失由独立测试断言，行为用例等待模块存在后执行。"""
    if importlib.util.find_spec("auto_git.repository_safety") is None:
        pytest.skip("等待 AGSAFE-02 仓库现场守门模块")
    return importlib.import_module("auto_git.repository_safety")


def test_repository_safety_guard_is_available() -> None:
    """新增机器门禁必须提供能由计划和执行共用的稳定入口。"""
    assert importlib.util.find_spec("auto_git.repository_safety") is not None, (
        "缺少 AGSAFE-02 仓库现场守门模块"
    )
    module = importlib.import_module("auto_git.repository_safety")
    assert callable(module.ensure_safe_repository)
    assert issubclass(module.UnsafeRepositoryError, RuntimeError)


def _marker_path(repo: Path, marker: str) -> Path:
    """通过Git解析真实管理路径，同时适配普通仓库与worktree。"""
    path = Path(git(repo, "rev-parse", "--git-path", marker))
    return path if path.is_absolute() else repo / path


@pytest.mark.parametrize("action", ("configure_identity", "stage_commit", "push"))
def test_clean_attached_repository_accepts_writes(repo: Path, safety, action: str) -> None:
    """普通已附着分支不被新增门禁误拦。"""
    safety.ensure_safe_repository(inspect_repo(repo), action)


def test_new_directory_accepts_init(tmp_path: Path, safety) -> None:
    """真正独立的新目录仍可进入初始化计划。"""
    safety.ensure_safe_repository(inspect_repo(tmp_path), "init")
    assert not (tmp_path / ".git").exists()


@pytest.mark.parametrize("action", ("configure_identity", "stage_commit"))
def test_unborn_head_is_not_detached(tmp_path: Path, safety, action: str) -> None:
    """initial HEAD有合法符号分支，可配置身份并作首次提交。"""
    git(tmp_path, "init", "-b", "main")
    facts = inspect_repo(tmp_path)
    assert facts["head"] == "(initial)"
    assert facts["branch"] == "main"
    safety.ensure_safe_repository(facts, action)


def test_existing_repository_init_requires_reuse(repo: Path, safety) -> None:
    """已初始化项目应提示复用，不通过再次init改变仓库。"""
    original_head = git(repo, "rev-parse", "HEAD")
    with pytest.raises(safety.UnsafeRepositoryError, match="复用"):
        safety.ensure_safe_repository(inspect_repo(repo), "init")
    assert git(repo, "rev-parse", "HEAD") == original_head


def test_parent_repository_cannot_be_mistaken_for_new_project(repo: Path, safety) -> None:
    """子目录facts归一到父仓后也不能被当作新的初始化目标。"""
    nested = repo / "nested-project"
    nested.mkdir()
    with pytest.raises(safety.UnsafeRepositoryError, match="复用"):
        safety.ensure_safe_repository(inspect_repo(nested), "init")
    assert not (nested / ".git").exists()


def test_init_refuses_directory_containing_nested_repository(tmp_path: Path, safety) -> None:
    """独立外层目录中已有内层仓库时，要求先澄清边界。"""
    nested = tmp_path / "nested-repository"
    nested.mkdir()
    git(nested, "init", "-b", "main")
    with pytest.raises(safety.UnsafeRepositoryError, match="嵌套"):
        safety.ensure_safe_repository(inspect_repo(tmp_path), "init")
    assert not (tmp_path / ".git").exists()


def test_init_rechecks_parent_boundary_after_inspection(tmp_path: Path, safety) -> None:
    """盘点后父目录变成仓库，旧的非仓库事实不能继续初始化。"""
    target = tmp_path / "new-project"
    target.mkdir()
    facts = inspect_repo(target)
    git(tmp_path, "init", "-b", "main")
    with pytest.raises(safety.UnsafeRepositoryError, match="复用|父仓库"):
        safety.ensure_safe_repository(facts, "init")
    assert not (target / ".git").exists()


def test_init_refuses_existing_bare_repository(tmp_path: Path, safety) -> None:
    """没有worktree的bare仓也不能当作空目录重新初始化。"""
    git(tmp_path, "init", "--bare")
    with pytest.raises(safety.UnsafeRepositoryError, match="复用|仓库"):
        safety.ensure_safe_repository(inspect_repo(tmp_path), "init")


@pytest.mark.parametrize("action", WRITE_ACTIONS[1:])
def test_non_repository_refuses_ordinary_writes(tmp_path: Path, safety, action: str) -> None:
    """除了init，其余写动作需要已存在的正确仓库。"""
    with pytest.raises(safety.UnsafeRepositoryError, match="不是 Git 仓库"):
        safety.ensure_safe_repository(inspect_repo(tmp_path), action)


@pytest.mark.parametrize("action", WRITE_ACTIONS)
def test_detached_head_refuses_every_write(repo: Path, safety, action: str) -> None:
    """真实detached HEAD拒绝普通写动作，包括身份和远程修改。"""
    git(repo, "checkout", "--detach", "HEAD")
    facts = inspect_repo(repo)
    assert facts["branch"] == "(detached)"
    with pytest.raises(safety.UnsafeRepositoryError):
        safety.ensure_safe_repository(facts, action)


@pytest.mark.parametrize("operation", ("merge", "rebase", "cherry-pick", "revert", "bisect", "unknown"))
def test_reported_operation_refuses_writes(repo: Path, safety, operation: str) -> None:
    """已知和未知在途操作均不得由普通提交隐式完成。"""
    facts = inspect_repo(repo)
    facts["operation"] = operation
    with pytest.raises(safety.UnsafeRepositoryError, match="操作|进行|现场"):
        safety.ensure_safe_repository(facts, "stage_commit")


@pytest.mark.parametrize(
    ("marker", "directory"),
    (("MERGE_HEAD", False), ("rebase-merge", True), ("rebase-apply", True),
     ("CHERRY_PICK_HEAD", False), ("REVERT_HEAD", False),
     ("BISECT_LOG", False), ("BISECT_START", False), ("sequencer", True)),
)
def test_management_markers_are_rechecked(
    repo: Path, safety, marker: str, directory: bool,
) -> None:
    """facts遗漏标记或盘点后新增在途状态时仍应停止。"""
    facts = inspect_repo(repo)
    target = _marker_path(repo, marker)
    if directory:
        target.mkdir()
    else:
        target.write_text(git(repo, "rev-parse", "HEAD") + "\n", encoding="utf-8")
    with pytest.raises(safety.UnsafeRepositoryError, match="操作|进行|现场"):
        safety.ensure_safe_repository(facts, "configure_identity")


def test_worktree_uses_its_real_management_path(repo: Path, tmp_path: Path, safety) -> None:
    """worktree的.git是文件，仍能找到该worktree内的revert现场。"""
    worktree = tmp_path / "linked-worktree"
    git(repo, "worktree", "add", "-b", "linked", str(worktree))
    facts = inspect_repo(worktree)
    assert (worktree / ".git").is_file()
    _marker_path(worktree, "REVERT_HEAD").write_text(
        git(worktree, "rev-parse", "HEAD") + "\n", encoding="utf-8",
    )
    with pytest.raises(safety.UnsafeRepositoryError, match="revert"):
        safety.ensure_safe_repository(facts, "stage_commit")


def test_real_merge_conflict_refuses_write(repo: Path, safety) -> None:
    """真实分支冲突同时提供merge和unmerged事实。"""
    git(repo, "checkout", "-b", "side")
    (repo / "README.md").write_text("side\n", encoding="utf-8")
    git(repo, "add", "--", "README.md")
    git(repo, "commit", "-m", "支线修改")
    git(repo, "checkout", "main")
    (repo / "README.md").write_text("main\n", encoding="utf-8")
    git(repo, "add", "--", "README.md")
    git(repo, "commit", "-m", "主线修改")
    result = subprocess.run(["git", "merge", "side"], cwd=repo, capture_output=True, check=False)
    assert result.returncode != 0
    facts = inspect_repo(repo)
    assert any(item["kind"] == "unmerged" for item in facts["changes"])
    with pytest.raises(safety.UnsafeRepositoryError):
        safety.ensure_safe_repository(facts, "stage_commit")


@pytest.mark.parametrize("xy", ("UU", "AA", "DD", "AU", "UA", "UD", "DU"))
def test_unmerged_changes_refuse_writes_without_operation_marker(
    repo: Path, safety, xy: str,
) -> None:
    """即使operation缺失，冲突路径仍独立阻断。"""
    facts = inspect_repo(repo)
    facts["changes"] = [{"kind": "unmerged", "xy": xy, "path": "conflict.txt"}]
    with pytest.raises(safety.UnsafeRepositoryError, match="合并|冲突"):
        safety.ensure_safe_repository(facts, "stage_commit")


@pytest.mark.parametrize("action", ("inspect", "doctor", "history", "verify", "review"))
def test_read_only_actions_remain_available(repo: Path, safety, action: str) -> None:
    """不安全现场仍允许读取和解释，不会自动完成恢复。"""
    facts = inspect_repo(repo)
    facts.update(operation="merge", branch="(detached)")
    safety.ensure_safe_repository(facts, action)


def test_incomplete_branch_facts_fail_closed(repo: Path, safety) -> None:
    """缺失分支事实不能被当作已附着的安全分支。"""
    facts = inspect_repo(repo)
    facts["branch"] = None
    with pytest.raises(safety.UnsafeRepositoryError, match="分支"):
        safety.ensure_safe_repository(facts, "stage_commit")
