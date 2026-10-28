"""环境 doctor、安装策略与 CLI 合同测试。"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from auto_git.doctor import doctor
from auto_git.install import dependency_plan, skill_lifecycle_plan
from auto_git.manifest import build_manifest, verify_manifest

from conftest import git


def test_doctor_reports_capabilities_without_credentials(tmp_path: Path) -> None:
    result = doctor(tmp_path)
    assert result["schema_version"] == "1"
    assert {"python", "git", "gh", "github_auth", "identity"} <= result[
        "capabilities"
    ].keys()
    assert "token" not in json.dumps(result).lower()


def test_install_plan_is_guidance_not_root_execution() -> None:
    plan = dependency_plan("git", system="darwin")
    assert plan["requires_approval"] is True
    assert plan["automatic_root_install"] is False
    assert plan["verify_argv"][0] == "git"


def test_skill_lifecycle_plan_blocks_implicit_global() -> None:
    plan = skill_lifecycle_plan(
        "install",
        scope="project",
        source="wukongai/auto-git",
        target=".agents/skills/auto-git",
    )
    assert plan["requires_approval"] is True
    assert plan["scope"] == "project"
    assert plan["automatic_global_install"] is False


def test_release_archive_manifest_round_trip(tmp_path: Path) -> None:
    (tmp_path / "SKILL.md").write_text("skill\n", encoding="utf-8")
    script = tmp_path / "scripts" / "auto_git.py"
    script.parent.mkdir()
    script.write_text("print('ok')\n", encoding="utf-8")
    manifest = build_manifest(tmp_path, ["SKILL.md", "scripts/auto_git.py"])
    assert verify_manifest(tmp_path, manifest)["verified"] is True
    script.write_text("drift\n", encoding="utf-8")
    assert verify_manifest(tmp_path, manifest)["verified"] is False


def test_cli_inspect_json(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "auto_git.py"
    completed = subprocess.run(
        [sys.executable, str(script), "inspect", "--repo", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["is_repo"] is False


def test_cli_plan_and_apply_exact_commit(repo: Path, tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "auto_git.py"
    (repo / "cli.txt").write_text("cli\n", encoding="utf-8")
    plan_path = tmp_path / "plan.json"
    planned = subprocess.run(
        [
            sys.executable,
            str(script),
            "plan",
            "--repo",
            str(repo),
            "--action",
            "stage_commit",
            "--params-json",
            json.dumps({"paths": ["cli.txt"], "message": "feat: CLI 提交"}),
            "--output",
            str(plan_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    plan = json.loads(planned.stdout)
    applied = subprocess.run(
        [
            sys.executable,
            str(script),
            "apply",
            "--plan",
            str(plan_path),
            "--approval",
            plan["plan_hash"],
            "--state-home",
            str(tmp_path / "state"),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(applied.stdout)["status"] == "succeeded"


def test_cli_verify_mirrors_reads_two_remote_oids(repo: Path, tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "auto_git.py"
    github = tmp_path / "github.git"
    gitee = tmp_path / "gitee.git"
    for bare in (github, gitee):
        bare.mkdir()
        git(bare, "init", "--bare")
    git(repo, "remote", "add", "origin", str(github))
    git(repo, "remote", "add", "gitee", str(gitee))
    git(repo, "push", "origin", "HEAD:refs/heads/main")
    git(repo, "push", "gitee", "HEAD:refs/heads/main")

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "verify-mirrors",
            "--repo",
            str(repo),
            "--remote",
            "origin",
            "--remote",
            "gitee",
            "--branch",
            "main",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["verified"] is True
    assert payload["branches"]["origin"] == payload["branches"]["gitee"]


def test_cli_json_failure_is_stable_and_has_no_traceback(repo: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "auto_git.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "verify-mirrors",
            "--repo",
            str(repo),
            "--remote",
            "origin",
            "--remote",
            "gitee",
            "--branch",
            "main",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["status"] == "error"
    assert payload["error"]["type"] == "RemoteError"
    assert "Traceback" not in completed.stdout + completed.stderr


def test_cli_argument_failure_honors_json_contract() -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "auto_git.py"
    completed = subprocess.run(
        [sys.executable, str(script), "inspect", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["status"] == "error"
    assert payload["error"]["type"] == "ArgumentError"
    assert completed.stderr == ""


def test_cli_without_json_uses_human_readable_output(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "auto_git.py"
    completed = subprocess.run(
        [sys.executable, str(script), "inspect", "--repo", str(tmp_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "仓库" in completed.stdout
    with pytest.raises(json.JSONDecodeError):
        json.loads(completed.stdout)


def test_cli_exposes_dependency_auth_release_and_history(
    repo: Path,
    tmp_path: Path,
) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "auto_git.py"
    dependency = subprocess.run(
        [
            sys.executable,
            str(script),
            "dependency-plan",
            "--dependency",
            "git",
            "--system",
            "darwin",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(dependency.stdout)["automatic_root_install"] is False

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    gh = fake_bin / "gh"
    gh.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "if args[:2] == ['api', 'user']:\n"
        " print('owner')\n"
        "elif args[:2] == ['config', 'get']:\n"
        " print('https')\n",
        encoding="utf-8",
    )
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    auth = subprocess.run(
        [
            sys.executable,
            str(script),
            "auth-status",
            "--provider",
            "github",
            "--json",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert json.loads(auth.stdout)["authenticated"] is True

    bare = tmp_path / "release.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    git(repo, "remote", "add", "origin", str(bare))
    (repo / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (repo / "CHANGELOG.md").write_text("## 0.1.0\n", encoding="utf-8")
    git(repo, "add", "--", "VERSION", "CHANGELOG.md")
    git(repo, "commit", "-m", "chore: release check")
    git(repo, "push", "--set-upstream", "origin", "main")
    profile = {
        "version_file": "VERSION",
        "changelog_file": "CHANGELOG.md",
        "changelog_section": "## {version}",
        "allowed_branches": ["main"],
        "tag_template": "v{version}",
        "remote": "origin",
        "required_assets": ["README.md"],
        "draft": False,
        "prerelease": False,
        "regression": [[sys.executable, "-c", "print('fixture regression')"]],
        "build": [[sys.executable, "-c", "print('fixture build')"]],
    }
    release = subprocess.run(
        [
            sys.executable,
            str(script),
            "release-check",
            "--repo",
            str(repo),
            "--version",
            "0.1.0",
            "--profile-json",
            json.dumps(profile),
            "--regression-json",
            json.dumps(profile["regression"]),
            "--build-json",
            json.dumps(profile["build"]),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(release.stdout)["ready"] is True

    state_home = tmp_path / "state"
    record_dir = state_home / "records"
    record_dir.mkdir(parents=True)
    (record_dir / "plan-one.json").write_text(
        json.dumps(
            {
                "schema_version": "1",
                "plan_id": "plan-one",
                "repo": str(repo.resolve()),
                "action": "stage_commit",
                "status": "succeeded",
                "details": {"head": git(repo, "rev-parse", "HEAD")},
                "completed_at": "2026-08-03T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    history = subprocess.run(
        [
            sys.executable,
            str(script),
            "history",
            "--repo",
            str(repo),
            "--state-home",
            str(state_home),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(history.stdout)["operations"][0]["plan_id"] == "plan-one"
