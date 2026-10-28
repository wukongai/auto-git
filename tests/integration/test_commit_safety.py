"""提交范围、暂存后检查及失败保全的安全回归。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import auto_git.commit_execution as commit_execution
from auto_git.commit_execution import CommitSafetyError, execute_commit, verify_commit
from auto_git.planner import create_plan
from auto_git.regression import RegressionError, run_regression
from conftest import git

def commit_plan(repo: Path, paths: list[str], **params) -> dict:
    """为临时仓库创建真实、独立审批的精确 Commit 计划。"""
    return create_plan("stage_commit", repo, {
        "paths": paths, "message": "test: 验证安全提交", **params,
    })


def hook(repo: Path, body: str, name: str = "pre-commit") -> None:
    """仅向临时仓库安装本用例需要的 hook。"""
    target = repo / ".git/hooks" / name
    target.write_text("#!/bin/sh\nset -e\n" + body, encoding="utf-8")
    target.chmod(0o755)


def test_empty_regression_cannot_claim_checks_ran(repo: Path) -> None:
    with pytest.raises(RegressionError, match="至少|不能为空"):
        run_regression([], repo)


def test_code_without_project_checks_blocks_commit(repo: Path, tmp_path: Path) -> None:
    before = git(repo, "rev-parse", "HEAD")
    (repo / "feature.py").write_text("print('feature')\n", encoding="utf-8")
    with pytest.raises(CommitSafetyError, match="项目回归") as caught:
        execute_commit(repo, commit_plan(repo, ["feature.py"]), tmp_path / "state")
    assert caught.value.commit_created is False
    assert git(repo, "rev-parse", "HEAD") == before
    assert (repo / "feature.py").is_file()


def test_document_commit_runs_staged_integrity(repo: Path, tmp_path: Path) -> None:
    (repo / "README.md").write_text("# 文档更新\n", encoding="utf-8")
    details = execute_commit(repo, commit_plan(repo, ["README.md"]), tmp_path / "state")
    assert details["checks"]["profile"] == "integrity"
    assert details["checks"]["business_correctness_proven"] is False
    assert details["checks"]["results"][0]["argv"] == ["git", "diff", "--cached", "--check"]
    assert details["checks"]["results"][0]["returncode"] == 0
    assert details["commit_evidence"]["staged_tree"] == git(repo, "rev-parse", "HEAD^{tree}")
    assert verify_commit(repo, details) is True


def test_unstaged_whitespace_is_checked_after_staging(repo: Path, tmp_path: Path) -> None:
    before = git(repo, "rev-parse", "HEAD")
    (repo / "README.md").write_text("bad trailing whitespace  \n", encoding="utf-8")
    with pytest.raises(CommitSafetyError) as caught:
        execute_commit(repo, commit_plan(repo, ["README.md"]), tmp_path / "state")
    assert caught.value.commit_created is False
    assert caught.value.details["checks"]["results"][0]["returncode"] != 0
    assert git(repo, "rev-parse", "HEAD") == before
    assert git(repo, "diff", "--cached", "--name-only") == ""


def test_hook_cannot_expand_approved_commit_paths(repo: Path, tmp_path: Path) -> None:
    (repo / "README.md").write_text("# 批准\n", encoding="utf-8")
    (repo / "outside.txt").write_text("范围外\n", encoding="utf-8")
    hook(repo, "git add -- outside.txt\n")
    with pytest.raises(CommitSafetyError) as caught:
        execute_commit(repo, commit_plan(repo, ["README.md"]), tmp_path / "state")
    assert caught.value.commit_created is True
    details = caught.value.details
    assert details["status"] == "verification_failed"
    assert details["head"] == git(repo, "rev-parse", "HEAD")
    assert details["commit_evidence"]["actual_paths"] == ["README.md", "outside.txt"]
    assert verify_commit(repo, details) is False


def test_hook_cannot_replace_approved_file_content(repo: Path, tmp_path: Path) -> None:
    (repo / "README.md").write_text("# 批准内容\n", encoding="utf-8")
    hook(repo, "printf 'hook changed content\\n' > README.md\ngit add -- README.md\n")
    with pytest.raises(CommitSafetyError) as caught:
        execute_commit(repo, commit_plan(repo, ["README.md"]), tmp_path / "state")
    assert caught.value.commit_created is True
    evidence = caught.value.details["commit_evidence"]
    assert evidence["actual_tree"] != evidence["staged_tree"]
    assert "hook changed content" in (repo / "README.md").read_text(encoding="utf-8")


def test_hook_worktree_side_effect_is_not_reported_success(repo: Path, tmp_path: Path) -> None:
    (repo / "README.md").write_text("# 批准\n", encoding="utf-8")
    hook(repo, "printf 'side effect\\n' > generated.txt\n")
    with pytest.raises(CommitSafetyError) as caught:
        execute_commit(repo, commit_plan(repo, ["README.md"]), tmp_path / "state")
    assert caught.value.commit_created is True
    assert caught.value.details["commit_evidence"]["workspace_changed"] is True
    assert (repo / "generated.txt").is_file()


def test_failed_hook_keeps_hook_changed_index(repo: Path, tmp_path: Path) -> None:
    before = git(repo, "rev-parse", "HEAD")
    (repo / "README.md").write_text("# 批准\n", encoding="utf-8")
    (repo / "outside.txt").write_text("保留 hook 已暂存内容\n", encoding="utf-8")
    hook(repo, "git add -- outside.txt\nexit 1\n")
    with pytest.raises(CommitSafetyError) as caught:
        execute_commit(repo, commit_plan(repo, ["README.md"]), tmp_path / "state")
    assert git(repo, "rev-parse", "HEAD") == before
    assert git(repo, "diff", "--cached", "--name-only").splitlines() == ["README.md", "outside.txt"]
    assert caught.value.commit_created is False
    assert caught.value.details["index_restored"] is False


def test_project_check_side_effect_blocks_commit_and_preserves_files(repo: Path, tmp_path: Path) -> None:
    before = git(repo, "rev-parse", "HEAD")
    (repo / "feature.py").write_text("print('feature')\n", encoding="utf-8")
    command = [sys.executable, "-c", "from pathlib import Path; Path('generated.txt').write_text('side effect')"]
    with pytest.raises(CommitSafetyError) as caught:
        execute_commit(repo, commit_plan(repo, ["feature.py"], regression=[command]), tmp_path / "state")
    assert caught.value.commit_created is False
    assert git(repo, "rev-parse", "HEAD") == before
    assert (repo / "generated.txt").is_file()


def test_code_commit_preserves_check_evidence_and_independent_verification(repo: Path, tmp_path: Path) -> None:
    (repo / "feature.py").write_text("print('feature')\n", encoding="utf-8")
    checks = [[sys.executable, "-c", "print('project check passed')"]]
    details = execute_commit(repo, commit_plan(repo, ["feature.py"], regression=checks), tmp_path / "state")
    assert details["checks"]["profile"] == "project"
    assert len(details["checks"]["results"]) == 2
    assert details["index_backup_checksum"]
    assert details["post_index_checksum"]
    assert verify_commit(repo, details) is True
    details["commit_evidence"]["staged_tree"] = "0" * 40
    assert verify_commit(repo, details) is False


def test_old_record_without_commit_evidence_is_not_certified(repo: Path) -> None:
    assert verify_commit(repo, {"head": git(repo, "rev-parse", "HEAD")}) is False


def test_invalid_record_base_is_rejected_before_git_io(repo: Path, monkeypatch) -> None:
    """伪造记录的对象身份不能作为 Git 选项进入运行器。"""
    def unexpected_io(*_args, **_kwargs):
        raise AssertionError("非法对象身份不应触发 Git I/O")

    details = {
        "head": "a" * 40, "paths": ["README.md"], "status": "succeeded",
        "checks": {"results": [{"returncode": 0}]},
        "commit_evidence": {
            "base_head": "--stat", "staged_tree": "b" * 40, "actual_tree": "b" * 40,
            "actual_paths": ["README.md"], "actual_parents": ["--stat"],
            "workspace_changed": False, "post_index_tree": "b" * 40,
            "post_index_matches_commit": True, "index_verification_scope": "captured_post_commit",
        },
    }
    monkeypatch.setattr(commit_execution, "run", unexpected_io)
    assert verify_commit(repo, details) is False


def test_visible_sensitive_path_blocks_without_reading_body(repo: Path, tmp_path: Path, monkeypatch) -> None:
    """路径盘点可以发现敏感文件，但不得读取其正文。"""
    (repo / "README.md").write_text("# approved\n", encoding="utf-8")
    plan = commit_plan(repo, ["README.md"])
    (repo / ".env").write_text("fixture-value\n", encoding="utf-8")
    original = commit_execution._update_path_digest

    def guarded_digest(digest, root, relative):
        assert relative != ".env", "不允许读取敏感正文"
        return original(digest, root, relative)

    monkeypatch.setattr(commit_execution, "_update_path_digest", guarded_digest)
    with pytest.raises(CommitSafetyError, match="敏感路径") as caught:
        execute_commit(repo, plan, tmp_path / "state")
    assert caught.value.commit_created is False
    assert caught.value.details["sensitive_paths"] == [".env"]
    assert git(repo, "diff", "--cached", "--name-only") == ""


def test_hook_creating_sensitive_path_is_preserved_without_body_read(repo: Path, tmp_path: Path, monkeypatch) -> None:
    """hook 新建敏感路径时只记录路径和已发生事实。"""
    (repo / "README.md").write_text("# approved\n", encoding="utf-8")
    hook(repo, "printf 'fixture-value\\n' > .env\n")
    original = commit_execution._update_path_digest

    def guarded_digest(digest, root, relative):
        assert relative != ".env", "不允许读取敏感正文"
        return original(digest, root, relative)

    monkeypatch.setattr(commit_execution, "_update_path_digest", guarded_digest)
    with pytest.raises(CommitSafetyError, match="敏感路径") as caught:
        execute_commit(repo, commit_plan(repo, ["README.md"]), tmp_path / "state")
    assert caught.value.commit_created is True
    assert caught.value.details["sensitive_paths"] == [".env"]
    assert caught.value.details["status"] == "verification_failed"
    assert (repo / ".env").is_file()


@pytest.mark.parametrize(("value", "sensitive"), [
    (".env", True), ("config/.env.production", True), ("config/private.pem", True),
    ("signing.key", True), ("id_ed25519", True), ("config/credentials.json", True),
    (".ssh/config", True), ("config/secrets.yaml", True),
    (".env.example", False), (".env.sample", False), (".env.template", False),
    ("README.md", False), ("source/keyboard.py", False),
])
def test_sensitive_path_classifier_uses_names_only(value: str, sensitive: bool) -> None:
    """路径判定不打开文件，示例放行也不等于正文无凭证。"""
    try:
        from auto_git.sensitive_paths import is_sensitive_path
    except ModuleNotFoundError:
        pytest.fail("尚未实现共享敏感路径判定器")
    assert is_sensitive_path(value) is sensitive


def test_post_commit_hook_cannot_leave_outside_file_staged(repo: Path, tmp_path: Path) -> None:
    """post-commit 只改 index 也属于本次操作副作用，保留现场但不能成功。"""
    (repo / "README.md").write_text("# approved\n", encoding="utf-8")
    (repo / "outside.md").write_text("# remains outside\n", encoding="utf-8")
    hook(repo, "git add -- outside.md\n", name="post-commit")
    with pytest.raises(CommitSafetyError) as caught:
        execute_commit(repo, commit_plan(repo, ["README.md"]), tmp_path / "state")
    error = caught.value
    assert error.commit_created is True
    assert error.details["status"] == "verification_failed"
    assert error.details["head"] == git(repo, "rev-parse", "HEAD")
    evidence = error.details["commit_evidence"]
    assert evidence["actual_paths"] == ["README.md"]
    assert evidence["post_index_tree"] != evidence["actual_tree"]
    assert evidence["post_index_matches_commit"] is False
    assert git(repo, "diff", "--cached", "--name-only") == "outside.md"
    assert verify_commit(repo, error.details) is False


def test_verify_certifies_captured_index_without_claiming_current_index_unchanged(repo: Path, tmp_path: Path) -> None:
    """后续合法暂存不改变历史认证，伪造不一致的已捕获 index 则不得认证。"""
    (repo / "README.md").write_text("# approved\n", encoding="utf-8")
    details = execute_commit(repo, commit_plan(repo, ["README.md"]), tmp_path / "state")
    assert details["commit_evidence"]["index_verification_scope"] == "captured_post_commit"
    assert details["commit_evidence"]["post_index_matches_commit"] is True
    (repo / "later.md").write_text("# later work\n", encoding="utf-8")
    git(repo, "add", "--", "later.md")
    assert verify_commit(repo, details) is True
    details["commit_evidence"]["post_index_tree"] = "0" * 40
    assert verify_commit(repo, details) is False
