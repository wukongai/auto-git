"""Push检查和远端已写入后的不确定结果必须可独立核验。"""

from pathlib import Path
import json
import subprocess

import pytest

from conftest import git
from auto_git.executor import apply_plan
from auto_git.planner import create_plan
from auto_git.runner import CommandError, CommandResult


def connect(repo: Path, tmp_path: Path) -> Path:
    """只连接临时本地bare远端。"""
    target = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(target)], check=True, capture_output=True)
    git(repo, "remote", "add", "origin", str(target))
    return target


def test_code_push_without_project_regression_never_writes(repo: Path, tmp_path: Path) -> None:
    """已有代码提交同样不能在缺少检查时公开。"""
    remote = connect(repo, tmp_path)
    (repo / "main.py").write_text("print('code')\n")
    git(repo, "add", "--", "main.py")
    git(repo, "commit", "-m", "test: 代码提交夹具")
    plan = create_plan("push", repo, {"remote": "origin", "branch": "main"})
    with pytest.raises(RuntimeError, match="回归|检查"):
        apply_plan(plan, approval=plan["plan_hash"], state_home=tmp_path / "state")
    assert not git(remote, "for-each-ref", "refs/heads/main")


def test_push_postflight_disconnect_keeps_unknown_and_can_verify(repo: Path, tmp_path: Path, monkeypatch) -> None:
    """远端实际收到之后核验断线，记录必须保留且禁止盲重放。"""
    import auto_git.remote as remote_module
    from auto_git.verification import verify_record
    remote = connect(repo, tmp_path)
    plan = create_plan("push", repo, {"remote": "origin", "branch": "main"})
    state = tmp_path / "state"
    original = remote_module.run
    sent = False

    def disconnect(argv, **kwargs):
        nonlocal sent
        if sent and "ls-remote" in argv:
            raise CommandError(CommandResult(tuple(argv), 128, "", "fixture disconnected"))
        result = original(argv, **kwargs)
        if argv[:2] == ["git", "push"]:
            sent = True
        return result

    monkeypatch.setattr(remote_module, "run", disconnect)
    with pytest.raises(RuntimeError):
        apply_plan(plan, approval=plan["plan_hash"], state_home=state)
    assert git(remote, "rev-parse", "refs/heads/main") == plan["params"]["remote_preflight"]["local_head"]
    record = json.loads((state / "records" / f"{plan['id']}.json").read_text())
    assert record["status"] == "unknown"
    assert record["next_step"]
    monkeypatch.setattr(remote_module, "run", original)
    verified = verify_record(record)
    assert verified["verified"] is False
    assert verified["verification_status"] == "partial"
    assert verified["remote_applied"] is True
    with pytest.raises(RuntimeError, match="记录|重放|核验"):
        apply_plan(plan, approval=plan["plan_hash"], state_home=state)


def test_push_success_record_rechecks_local_upstream(repo: Path, tmp_path: Path) -> None:
    """历史成功不能认证之后被移除的上游配置。"""
    from auto_git.verification import verify_record
    connect(repo, tmp_path)
    plan = create_plan("push", repo, {"remote": "origin", "branch": "main"})
    record = apply_plan(plan, approval=plan["plan_hash"], state_home=tmp_path / "state")
    assert verify_record(record)["verified"] is True
    git(repo, "branch", "--unset-upstream", "main")
    result = verify_record(record)
    assert result["verified"] is False
    assert result["remote_applied"] is True
