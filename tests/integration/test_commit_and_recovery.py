"""精确 staging、回归、Commit 和恢复集成测试。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import auto_git.executor as executor_module
import auto_git.recovery as recovery_module
from auto_git.executor import ApplyError, apply_plan, verify_record
from auto_git.planner import create_plan
from auto_git.recovery import create_recovery_plan

from conftest import git


def test_exact_commit_does_not_stage_unapproved_file(repo: Path, tmp_path: Path) -> None:
    (repo / "approved.txt").write_text("yes\n", encoding="utf-8")
    (repo / "not-approved.txt").write_text("no\n", encoding="utf-8")
    plan = create_plan(
        "stage_commit",
        repo,
        {
            "paths": ["approved.txt"],
            "message": "feat: 精确提交",
            "regression": [["python3", "-c", "print('pass')"]],
        },
    )
    record = apply_plan(plan, approval=plan["plan_hash"], state_home=tmp_path / "state")
    assert record["status"] == "succeeded"
    assert git(repo, "show", "--pretty=", "--name-only", "HEAD") == "approved.txt"
    assert "not-approved.txt" in git(repo, "status", "--porcelain")


def test_regression_failure_blocks_commit(repo: Path, tmp_path: Path) -> None:
    (repo / "blocked.txt").write_text("blocked\n", encoding="utf-8")
    before = git(repo, "rev-parse", "HEAD")
    plan = create_plan(
        "stage_commit",
        repo,
        {
            "paths": ["blocked.txt"],
            "message": "不应提交",
            "regression": [["python3", "-c", "raise SystemExit(9)"]],
        },
    )
    with pytest.raises(ApplyError, match="回归"):
        apply_plan(plan, approval=plan["plan_hash"], state_home=tmp_path / "state")
    assert git(repo, "rev-parse", "HEAD") == before


def test_regression_side_effect_causes_drift_block(repo: Path, tmp_path: Path) -> None:
    (repo / "approved.txt").write_text("approved\n", encoding="utf-8")
    before = git(repo, "rev-parse", "HEAD")
    plan = create_plan(
        "stage_commit",
        repo,
        {
            "paths": ["approved.txt"],
            "message": "不应提交",
            "regression": [
                [
                    "python3",
                    "-c",
                    "from pathlib import Path; Path('generated.txt').write_text('drift')",
                ]
            ],
        },
    )
    with pytest.raises(ApplyError, match="漂移"):
        apply_plan(plan, approval=plan["plan_hash"], state_home=tmp_path / "state")
    assert git(repo, "rev-parse", "HEAD") == before


def test_wrong_approval_and_drift_are_blocked(repo: Path, tmp_path: Path) -> None:
    plan = create_plan("stage_commit", repo, {"paths": ["README.md"], "message": "测试"})
    with pytest.raises(ApplyError, match="审批"):
        apply_plan(plan, approval="wrong", state_home=tmp_path / "state")
    (repo / "drift.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(ApplyError, match="漂移"):
        apply_plan(plan, approval=plan["plan_hash"], state_home=tmp_path / "state")


def test_apply_is_idempotent_when_existing_record_still_verifies(
    repo: Path,
    tmp_path: Path,
) -> None:
    (repo / "once.txt").write_text("once\n", encoding="utf-8")
    plan = create_plan(
        "stage_commit",
        repo,
        {"paths": ["once.txt"], "message": "feat: 只执行一次"},
    )
    state_home = tmp_path / "state"
    first = apply_plan(plan, approval=plan["plan_hash"], state_home=state_home)
    first_head = git(repo, "rev-parse", "HEAD")

    replay = apply_plan(plan, approval=plan["plan_hash"], state_home=state_home)

    assert git(repo, "rev-parse", "HEAD") == first_head
    assert replay["plan_id"] == first["plan_id"]
    assert replay["idempotent_replay"] is True
    persisted = json.loads(
        (state_home / "records" / f"{plan['id']}.json").read_text(encoding="utf-8")
    )
    assert "idempotent_replay" not in persisted


def test_apply_blocks_replay_when_existing_record_postcondition_drifted(
    repo: Path,
    tmp_path: Path,
) -> None:
    (repo / "once.txt").write_text("once\n", encoding="utf-8")
    plan = create_plan(
        "stage_commit",
        repo,
        {"paths": ["once.txt"], "message": "feat: 原始执行"},
    )
    state_home = tmp_path / "state"
    apply_plan(plan, approval=plan["plan_hash"], state_home=state_home)
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    git(repo, "add", "--", "later.txt")
    git(repo, "commit", "-m", "feat: 后续提交")

    with pytest.raises(ApplyError, match="record.*漂移|记录.*漂移"):
        apply_plan(plan, approval=plan["plan_hash"], state_home=state_home)


def test_apply_revalidates_repository_after_lock_is_acquired(
    repo: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    plan = create_plan(
        "configure_identity",
        repo,
        {"scope": "local", "name": "Changed", "email": "changed@example.invalid"},
    )
    original_lock = executor_module.RepositoryLock

    class DriftingLock(original_lock):
        def __enter__(self):
            held = super().__enter__()
            (repo / "after-lock.txt").write_text("drift\n", encoding="utf-8")
            return held

    monkeypatch.setattr(executor_module, "RepositoryLock", DriftingLock)
    with pytest.raises(ApplyError, match="漂移"):
        apply_plan(
            plan,
            approval=plan["plan_hash"],
            state_home=tmp_path / "state",
        )
    assert git(repo, "config", "--get", "user.name") == "Auto Git Test"


def test_recover_index_requires_plan_approval_and_unchanged_state(
    repo: Path,
    tmp_path: Path,
) -> None:
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    state_home = tmp_path / "state"
    commit_plan = create_plan(
        "stage_commit",
        repo,
        {"paths": ["a.txt"], "message": "feat: 用于恢复测试"},
    )
    record = apply_plan(
        commit_plan,
        approval=commit_plan["plan_hash"],
        state_home=state_home,
    )
    record_path = state_home / "records" / f"{record['plan_id']}.json"
    recovery_plan = create_recovery_plan(
        record_path,
        repo=repo,
        state_home=state_home,
    )

    with pytest.raises(ApplyError, match="审批"):
        apply_plan(recovery_plan, approval="wrong", state_home=state_home)

    recovery_record = apply_plan(
        recovery_plan,
        approval=recovery_plan["plan_hash"],
        state_home=state_home,
    )
    backup = Path(record["details"]["index_backup"])
    assert (repo / ".git" / "index").read_bytes() == backup.read_bytes()
    assert Path(recovery_record["details"]["undo_backup"]).is_file()
    assert verify_record(recovery_record)["verified"] is True
    (repo / "after-recovery.txt").write_text("drift\n", encoding="utf-8")
    git(repo, "add", "--", "after-recovery.txt")
    assert verify_record(recovery_record)["verified"] is False


def test_recovery_plan_rejects_unowned_or_tampered_record(
    repo: Path,
    tmp_path: Path,
) -> None:
    state_home = tmp_path / "state"
    outside = tmp_path / "forged.json"
    outside.write_text(
        '{"schema_version":"1","owned":true,"repo":"%s"}' % repo,
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="记录"):
        create_recovery_plan(outside, repo=repo, state_home=state_home)

    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    plan = create_plan("stage_commit", repo, {"paths": ["a.txt"], "message": "feat: 记录"})
    record = apply_plan(plan, approval=plan["plan_hash"], state_home=state_home)
    checksum = (
        state_home / "index-backups" / f"{record['plan_id']}.index.sha256"
    )
    checksum.unlink()
    record_path = state_home / "records" / f"{record['plan_id']}.json"
    with pytest.raises(RuntimeError, match="checksum"):
        create_recovery_plan(record_path, repo=repo, state_home=state_home)


def test_recovery_plan_rejects_current_index_drift(repo: Path, tmp_path: Path) -> None:
    state_home = tmp_path / "state"
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    plan = create_plan("stage_commit", repo, {"paths": ["a.txt"], "message": "feat: 记录"})
    record = apply_plan(plan, approval=plan["plan_hash"], state_home=state_home)
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    git(repo, "add", "--", "later.txt")
    record_path = state_home / "records" / f"{record['plan_id']}.json"
    with pytest.raises(RuntimeError, match="index 已漂移"):
        create_recovery_plan(record_path, repo=repo, state_home=state_home)


def test_cli_recovery_requires_separate_plan_and_exact_approval(
    repo: Path,
    tmp_path: Path,
) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "auto_git.py"
    state_home = tmp_path / "state"
    (repo / "cli-recovery.txt").write_text("recovery\n", encoding="utf-8")
    commit_plan = create_plan(
        "stage_commit",
        repo,
        {"paths": ["cli-recovery.txt"], "message": "feat: recovery CLI"},
    )
    record = apply_plan(
        commit_plan,
        approval=commit_plan["plan_hash"],
        state_home=state_home,
    )
    record_path = state_home / "records" / f"{record['plan_id']}.json"
    recovery_plan_path = tmp_path / "recovery-plan.json"
    planned = subprocess.run(
        [
            sys.executable,
            str(script),
            "plan-recover",
            "--repo",
            str(repo),
            "--record",
            str(record_path),
            "--state-home",
            str(state_home),
            "--output",
            str(recovery_plan_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    recovery_plan = json.loads(planned.stdout)
    denied = subprocess.run(
        [
            sys.executable,
            str(script),
            "recover",
            "--plan",
            str(recovery_plan_path),
            "--approval",
            "wrong",
            "--state-home",
            str(state_home),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert denied.returncode == 2
    assert json.loads(denied.stdout)["status"] == "error"
    assert "Traceback" not in denied.stdout + denied.stderr

    restored = subprocess.run(
        [
            sys.executable,
            str(script),
            "recover",
            "--plan",
            str(recovery_plan_path),
            "--approval",
            recovery_plan["plan_hash"],
            "--state-home",
            str(state_home),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(restored.stdout)["details"]["restored"] is True


def test_recovery_atomic_replace_failure_preserves_current_index(
    repo: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_home = tmp_path / "state"
    (repo / "atomic.txt").write_text("atomic\n", encoding="utf-8")
    commit_plan = create_plan(
        "stage_commit",
        repo,
        {"paths": ["atomic.txt"], "message": "feat: atomic recovery"},
    )
    record = apply_plan(
        commit_plan,
        approval=commit_plan["plan_hash"],
        state_home=state_home,
    )
    recovery_plan = create_recovery_plan(
        state_home / "records" / f"{record['plan_id']}.json",
        repo=repo,
        state_home=state_home,
    )
    index = repo / ".git" / "index"
    before = index.read_bytes()

    def fail_replace(_source: object, _target: object) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr(recovery_module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failure"):
        apply_plan(
            recovery_plan,
            approval=recovery_plan["plan_hash"],
            state_home=state_home,
        )
    assert index.read_bytes() == before
