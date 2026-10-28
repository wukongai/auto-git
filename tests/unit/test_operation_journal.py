"""操作开始、失败及不确定结果必须留下可信记录。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import auto_git.executor as executor
from auto_git.planner import create_plan
from auto_git.runner import CommandError, CommandResult


def test_running_record_exists_before_first_local_write(repo: Path, tmp_path: Path, monkeypatch) -> None:
    """身份写入之前就应能读到running，而非成功后才建记录。"""
    plan = create_plan("configure_identity", repo, {"name": "Changed", "email": "changed@example.invalid"})
    state = tmp_path / "state"
    path = state / "records" / f"{plan['id']}.json"
    original = executor.run
    observed = []

    def observe(argv, **kwargs):
        if argv[:4] == ["git", "config", "--local", "user.name"]:
            observed.append(json.loads(path.read_text())["status"])
        return original(argv, **kwargs)

    monkeypatch.setattr(executor, "run", observe)
    result = executor.apply_plan(plan, approval=plan["plan_hash"], state_home=state)
    assert observed == ["running"]
    assert result["status"] == "succeeded"
    assert result["started_at"] <= result["completed_at"]


def test_partial_local_failure_is_persisted_and_not_replayed(repo: Path, tmp_path: Path, monkeypatch) -> None:
    """第二个身份字段失败时记录部分写入，不能盲重放。"""
    plan = create_plan("configure_identity", repo, {"name": "Changed", "email": "changed@example.invalid"})
    state = tmp_path / "state"
    original = executor.run

    def fail_email(argv, **kwargs):
        if argv[:4] == ["git", "config", "--local", "user.email"]:
            raise CommandError(CommandResult(tuple(argv), 1, "", "fixture failure"))
        return original(argv, **kwargs)

    monkeypatch.setattr(executor, "run", fail_email)
    with pytest.raises(executor.ApplyError):
        executor.apply_plan(plan, approval=plan["plan_hash"], state_home=state)
    path = state / "records" / f"{plan['id']}.json"
    record = json.loads(path.read_text())
    assert record["status"] == "partial"
    assert record["next_step"]
    assert "changed@example.invalid" not in path.read_text()
    with pytest.raises(executor.ApplyError, match="重放|核验|记录"):
        executor.apply_plan(plan, approval=plan["plan_hash"], state_home=state)


def test_remote_verifier_distinguishes_read_failure_from_drift(repo: Path, monkeypatch) -> None:
    """无法读取远端只意味着未知，不是已证明远端不同。"""
    from auto_git import verification
    original = verification.run

    def fail_remote(argv, **kwargs):
        if "ls-remote" in argv:
            return CommandResult(tuple(argv), 128, "", "fixture network unavailable")
        return original(argv, **kwargs)

    from conftest import git
    git(repo, "remote", "add", "origin", str(repo.parent / "not-read"))
    monkeypatch.setattr(verification, "run", fail_remote)
    record = {"repo": str(repo), "action": "push", "status": "unknown", "details": {"name": "origin", "branch": "main", "remote": "a" * 40}}
    result = verification.verify_record(record)
    assert result["verified"] is None
    assert result["verification_status"] == "unknown"


def test_failure_record_never_persists_arbitrary_diagnostic_body(repo: Path, tmp_path: Path) -> None:
    """Hook诊断可以包含完整diff，持久日志只能保存稳定错误摘要。"""
    from auto_git.operation_journal import OperationJournal
    plan = create_plan("configure_identity", repo, {"name": "Changed", "email": "changed@example.invalid"})
    journal = OperationJournal(plan, tmp_path / "state")
    journal.start()
    journal.failure(RuntimeError("diff --git a/a.md b/a.md\n+PRIVATE_FIXTURE_CONTENT"))
    persisted = journal.path.read_text()
    assert "diff --git" not in persisted
    assert "PRIVATE_FIXTURE_CONTENT" not in persisted
    assert json.loads(persisted)["error"]["type"] == "RuntimeError"


def test_tag_created_before_read_failure_is_unknown_not_unapplied(repo: Path, tmp_path: Path, monkeypatch) -> None:
    """Tag不进入工作区指纹，不能据指纹未变宣称完全未执行。"""
    from conftest import git
    from auto_git.verification import verify_record
    plan = create_plan("tag", repo, {"tag": "v-audit"})
    state = tmp_path / "state"
    original = executor.run
    created = False

    def fail_after_tag(argv, **kwargs):
        nonlocal created
        if created and argv[:2] == ["git", "rev-parse"]:
            raise CommandError(CommandResult(tuple(argv), 128, "", "fixture read failure"))
        result = original(argv, **kwargs)
        if argv[:2] == ["git", "tag"]:
            created = True
        return result

    monkeypatch.setattr(executor, "run", fail_after_tag)
    with pytest.raises(executor.ApplyError):
        executor.apply_plan(plan, approval=plan["plan_hash"], state_home=state)
    assert git(repo, "rev-parse", "refs/tags/v-audit^{commit}")
    record = json.loads((state / "records" / f"{plan['id']}.json").read_text())
    assert record["status"] == "unknown"
    assert verify_record(record)["verified"] is True
