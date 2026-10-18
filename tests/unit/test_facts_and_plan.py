"""仓库事实、porcelain v2 和不可变计划测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import git
from auto_git.git_facts import inspect_repo, parse_porcelain_v2_z
from auto_git.planner import PlanError, create_plan, validate_plan


def test_parse_porcelain_v2_nul_handles_spaces_and_untracked() -> None:
    raw = (
        b"# branch.oid abc\x00# branch.head main\x00"
        b"1 .M N... 100644 100644 100644 abc abc file with space.txt\x00"
        b"? new file.txt\x00"
    )
    facts = parse_porcelain_v2_z(raw)
    assert facts["branch"] == "main"
    assert facts["changes"][0]["path"] == "file with space.txt"
    assert facts["changes"][1] == {"kind": "untracked", "path": "new file.txt"}


def test_inspect_non_repo_is_machine_readable(tmp_path: Path) -> None:
    facts = inspect_repo(tmp_path)
    assert facts["schema_version"] == "1"
    assert facts["is_repo"] is False
    assert len(facts["fingerprint"]) == 64


def test_init_plan_fingerprint_captures_nested_file_mode_drift(
    tmp_path: Path,
) -> None:
    project = tmp_path / "new-project"
    nested = project / "tools"
    nested.mkdir(parents=True)
    script = nested / "run.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    script.chmod(0o644)
    plan = create_plan("init", project, {"branch": "main"})
    script.chmod(0o755)
    with pytest.raises(PlanError, match="漂移"):
        validate_plan(plan, current_repo=project)


def test_plan_hash_and_fingerprint_block_tampering(repo: Path) -> None:
    plan = create_plan("stage_commit", repo, {"paths": ["README.md"], "message": "测试"})
    validate_plan(plan)
    plan["params"]["message"] = "被篡改"
    with pytest.raises(PlanError, match="hash"):
        validate_plan(plan)


def test_plan_captures_repository_drift(repo: Path) -> None:
    plan = create_plan("stage_commit", repo, {"paths": ["README.md"], "message": "测试"})
    (repo / "later.txt").write_text("drift\n", encoding="utf-8")
    with pytest.raises(PlanError, match="漂移"):
        validate_plan(plan, current_repo=repo)


def test_plan_fingerprint_captures_untracked_content_drift(repo: Path) -> None:
    target = repo / "draft.txt"
    target.write_text("first\n", encoding="utf-8")
    plan = create_plan(
        "stage_commit",
        repo,
        {"paths": ["draft.txt"], "message": "docs: 保存草稿"},
    )
    target.write_text("second\n", encoding="utf-8")
    with pytest.raises(PlanError, match="漂移"):
        validate_plan(plan, current_repo=repo)


def test_plan_fingerprint_captures_local_config_and_remote_drift(repo: Path) -> None:
    plan = create_plan(
        "configure_identity",
        repo,
        {"scope": "local", "name": "New Name", "email": "new@example.invalid"},
    )
    git(repo, "config", "--local", "auto-git.test-marker", "changed")
    with pytest.raises(PlanError, match="漂移"):
        validate_plan(plan, current_repo=repo)


def test_plan_fingerprint_captures_effective_config_drift(
    repo: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    global_config = tmp_path / "global.gitconfig"
    global_config.write_text("[core]\n\thooksPath = hooks-a\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    plan = create_plan(
        "configure_identity",
        repo,
        {"scope": "local", "name": "New Name", "email": "new@example.invalid"},
    )
    global_config.write_text("[core]\n\thooksPath = hooks-b\n", encoding="utf-8")
    with pytest.raises(PlanError, match="漂移"):
        validate_plan(plan, current_repo=repo)


def test_plan_fingerprint_captures_untracked_file_mode_drift(repo: Path) -> None:
    target = repo / "tool.sh"
    target.write_text("#!/bin/sh\n", encoding="utf-8")
    target.chmod(0o644)
    plan = create_plan(
        "stage_commit",
        repo,
        {"paths": ["tool.sh"], "message": "feat: 添加工具"},
    )
    target.chmod(0o755)
    with pytest.raises(PlanError, match="漂移"):
        validate_plan(plan, current_repo=repo)


def test_plan_contains_complete_approval_contract(repo: Path) -> None:
    plan = create_plan(
        "stage_commit",
        repo,
        {"paths": ["README.md"], "message": "docs: 更新说明"},
    )
    assert plan["summary"]
    assert plan["risk"] == "medium"
    assert plan["expected_postconditions"]
    assert plan["rollback"]
    assert "expires_at" not in plan


@pytest.mark.parametrize(
    ("action", "params"),
    [
        ("configure_identity", {"scope": "global", "name": "A", "email": "a@b.test"}),
        ("stage_commit", {"paths": ["../outside"], "message": "bad"}),
        ("remote_connect", {"name": "", "url": "https://github.com/o/r.git"}),
        ("push", {"remote": "origin", "branch": "-bad"}),
        ("tag", {"tag": "../bad", "version": "0.1.0"}),
        ("github_repo_create", {"name": "owner/demo", "visibility": ""}),
        ("github_release", {"version": "0.1.0"}),
    ],
)
def test_plan_rejects_invalid_action_parameters(
    repo: Path,
    action: str,
    params: dict[str, object],
) -> None:
    with pytest.raises(PlanError):
        create_plan(action, repo, params)
