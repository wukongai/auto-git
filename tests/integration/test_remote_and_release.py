"""Remote、Push、GitHub adapter 与 Release 测试。"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from auto_git.github import GitHubError, auth_status, create_repository
from auto_git.executor import apply_plan, verify_record
from auto_git.planner import PlanError, create_plan
from auto_git.release import (
    ReleaseError,
    check_readiness,
    create_github_release,
    load_release_profile,
    release_status,
)
from auto_git.remote import (
    RemoteError,
    connect_remote,
    push_branch,
    remote_facts,
    verify_mirror_refs,
)

from conftest import git


def test_local_remote_push_and_postflight(repo: Path, tmp_path: Path) -> None:
    bare = tmp_path / "remote.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))
    result = push_branch(repo, "origin", "main")
    assert result["verified"] is True
    assert git(bare, "rev-parse", "refs/heads/main") == git(repo, "rev-parse", "HEAD")
    assert (
        git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
        == "origin/main"
    )
    assert remote_facts(repo, "origin")["ahead"] == 0


def test_remote_mismatch_and_divergence_block(repo: Path, tmp_path: Path) -> None:
    one = tmp_path / "one.git"
    two = tmp_path / "two.git"
    one.mkdir()
    two.mkdir()
    git(one, "init", "--bare")
    git(two, "init", "--bare")
    connect_remote(repo, "origin", str(one))
    with pytest.raises(RemoteError, match="不一致"):
        connect_remote(repo, "origin", str(two))


@pytest.mark.parametrize("name", ["", "-oProxyCommand=bad", "../outside", "bad name"])
def test_remote_names_reject_option_injection(repo: Path, name: str) -> None:
    with pytest.raises(RemoteError, match="Remote 名称"):
        connect_remote(repo, name, "https://example.invalid/repo.git")


def test_remote_url_is_positional_not_a_git_option(repo: Path) -> None:
    with pytest.raises(RemoteError, match="URL"):
        connect_remote(repo, "origin", "--mirror=fetch")
    assert git(repo, "remote") == ""


@pytest.mark.parametrize(
    "url",
    [
        "https://user:password@example.com/owner/repo.git",
        "https://example.com/owner/repo.git?" + "to" + "ken=" + "sec" + "ret",
        "https://example.com/owner/repo.git#token",
        "https://" + "gh" + "p_123456789012@example.com/owner/repo.git",
    ],
)
def test_remote_rejects_urls_that_can_persist_credentials(
    repo: Path,
    url: str,
) -> None:
    with pytest.raises(RemoteError, match="凭证|query|fragment"):
        connect_remote(repo, "origin", url)
    assert git(repo, "remote") == ""
    with pytest.raises(PlanError, match="凭证|query|fragment"):
        create_plan(
            "remote_connect",
            repo,
            {"name": "origin", "url": url},
        )


@pytest.mark.parametrize(
    ("url", "identity"),
    [
        (
            "https://github.com/owner/repo.git",
            "https://github.com/owner/repo.git",
        ),
        (
            "git@github.com:owner/repo.git",
            "ssh://github.com/owner/repo.git",
        ),
    ],
)
def test_remote_records_sanitized_identity_only(
    repo: Path,
    url: str,
    identity: str,
) -> None:
    result = connect_remote(repo, "origin", url)
    assert result["url_identity"] == identity
    assert "url" not in result


def test_push_blocks_when_fetch_fails(repo: Path, tmp_path: Path) -> None:
    missing = tmp_path / "missing.git"
    connect_remote(repo, "origin", str(missing))
    with pytest.raises(RemoteError, match="fetch"):
        push_branch(repo, "origin", "main")


def test_dual_remote_branch_and_annotated_tag_postflight(
    repo: Path,
    tmp_path: Path,
) -> None:
    github = tmp_path / "github.git"
    gitee = tmp_path / "gitee.git"
    for bare in (github, gitee):
        bare.mkdir()
        git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(github))
    connect_remote(repo, "gitee", str(gitee))
    push_branch(repo, "origin", "main")
    push_branch(repo, "gitee", "main")
    git(repo, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
    git(repo, "push", "origin", "refs/tags/v0.1.0")
    git(repo, "push", "gitee", "refs/tags/v0.1.0")

    result = verify_mirror_refs(
        repo,
        remotes=["origin", "gitee"],
        branch="main",
        tag="v0.1.0",
    )
    assert result["verified"] is True
    local_head = git(repo, "rev-parse", "HEAD")
    local_tag_target = git(repo, "rev-parse", "v0.1.0^{}")
    assert result["branches"] == {"origin": local_head, "gitee": local_head}
    assert result["tags"] == {"origin": local_tag_target, "gitee": local_tag_target}


def test_dual_remote_postflight_blocks_missing_branch(
    repo: Path,
    tmp_path: Path,
) -> None:
    github = tmp_path / "github.git"
    gitee = tmp_path / "gitee.git"
    for bare in (github, gitee):
        bare.mkdir()
        git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(github))
    connect_remote(repo, "gitee", str(gitee))
    push_branch(repo, "origin", "main")

    with pytest.raises(RemoteError, match="gitee"):
        verify_mirror_refs(
            repo,
            remotes=["origin", "gitee"],
            branch="main",
        )


def test_dual_remote_postflight_blocks_mismatched_branch_oid(
    repo: Path,
    tmp_path: Path,
) -> None:
    github = tmp_path / "github.git"
    gitee = tmp_path / "gitee.git"
    for bare in (github, gitee):
        bare.mkdir()
        git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(github))
    connect_remote(repo, "gitee", str(gitee))
    push_branch(repo, "origin", "main")
    push_branch(repo, "gitee", "main")
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    git(repo, "add", "--", "new.txt")
    git(repo, "commit", "-m", "feat: 新提交")
    push_branch(repo, "origin", "main")

    with pytest.raises(RemoteError, match="gitee"):
        verify_mirror_refs(repo, remotes=["origin", "gitee"], branch="main")


def test_dual_remote_postflight_blocks_tag_missing_mismatch_and_lightweight(
    repo: Path,
    tmp_path: Path,
) -> None:
    github = tmp_path / "github.git"
    gitee = tmp_path / "gitee.git"
    for bare in (github, gitee):
        bare.mkdir()
        git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(github))
    connect_remote(repo, "gitee", str(gitee))
    push_branch(repo, "origin", "main")
    push_branch(repo, "gitee", "main")
    git(repo, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
    git(repo, "push", "origin", "refs/tags/v0.1.0")

    with pytest.raises(RemoteError, match="gitee"):
        verify_mirror_refs(
            repo,
            remotes=["origin", "gitee"],
            branch="main",
            tag="v0.1.0",
        )

    git(repo, "tag", "lightweight", "v0.1.0^{}")
    git(repo, "push", "gitee", "refs/tags/lightweight:refs/tags/v0.1.0")
    with pytest.raises(RemoteError, match="gitee"):
        verify_mirror_refs(
            repo,
            remotes=["origin", "gitee"],
            branch="main",
            tag="v0.1.0",
        )

    git(repo, "push", "gitee", ":refs/tags/v0.1.0")
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    git(repo, "add", "--", "later.txt")
    git(repo, "commit", "-m", "feat: tag target 漂移")
    push_branch(repo, "origin", "main")
    push_branch(repo, "gitee", "main")
    git(repo, "tag", "-a", "other", "-m", "other")
    git(repo, "push", "gitee", "refs/tags/other:refs/tags/v0.1.0")
    with pytest.raises(RemoteError, match="gitee"):
        verify_mirror_refs(
            repo,
            remotes=["origin", "gitee"],
            branch="main",
            tag="v0.1.0",
        )


def test_dual_remote_postflight_rejects_duplicate_or_unknown_remote(repo: Path) -> None:
    with pytest.raises(RemoteError, match="重复"):
        verify_mirror_refs(
            repo,
            remotes=["origin", "origin", "gitee"],
            branch="main",
        )
    with pytest.raises(RemoteError, match="未配置"):
        verify_mirror_refs(
            repo,
            remotes=["origin", "-oProxyCommand=bad"],
            branch="main",
        )


def test_github_create_requires_visibility_and_never_pushes(repo: Path) -> None:
    with pytest.raises(GitHubError, match="visibility"):
        create_repository(repo, "owner/demo", visibility="")


@pytest.mark.parametrize(
    "name",
    ["", "-R/owner/demo", "../demo", "owner/../demo", "owner/bad name"],
)
def test_github_create_rejects_unsafe_repository_name(repo: Path, name: str) -> None:
    with pytest.raises(GitHubError, match="仓库名称"):
        create_repository(repo, name, visibility="private")


@pytest.mark.parametrize("tag", ["", "-oProxyCommand=bad", "../outside", "bad tag"])
def test_tag_action_rejects_unsafe_name(
    repo: Path,
    tag: str,
) -> None:
    with pytest.raises(PlanError, match="Tag 名称"):
        create_plan("tag", repo, {"tag": tag, "version": "0.1.0"})


def test_github_create_is_a_separate_approved_action_without_push(
    repo: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log = tmp_path / "gh.json"
    gh = fake_bin / "gh"
    gh.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "open(os.environ['FAKE_GH_LOG'], 'a').write(json.dumps(args) + '\\n')\n"
        "if args[:2] == ['api', 'user']:\n"
        " print('owner')\n"
        "elif args[:2] == ['config', 'get']:\n"
        " print('https')\n"
        "elif args[:2] == ['repo', 'view']:\n"
        " print(json.dumps({'nameWithOwner':'owner/demo','visibility':'PRIVATE',"
        "'url':'https://github.com/owner/demo'}))\n",
        encoding="utf-8",
    )
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_GH_LOG", str(log))
    monkeypatch.setenv("GH_HOST", "attacker.invalid")
    monkeypatch.setenv("GH_REPO", "attacker/redirect")
    plan = create_plan(
        "github_repo_create",
        repo,
        {"name": "owner/demo", "visibility": "private"},
    )
    record = apply_plan(
        plan,
        approval=plan["plan_hash"],
        state_home=tmp_path / "state",
    )
    calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert record["details"]["pushed"] is False
    assert record["details"]["verified"] is True
    assert record["details"]["authenticated_account"] == "owner"
    assert all("--push" not in argv for argv in calls)
    assert any(argv[:2] == ["repo", "view"] for argv in calls)
    assert record["details"]["hostname"] == "github.com"

    status = auth_status()
    assert status["authenticated"] is True
    assert status["account"] == "owner"
    assert status["git_protocol"] == "https"


def test_release_readiness_and_verify_tag(repo: Path, tmp_path: Path, monkeypatch) -> None:
    bare = tmp_path / "release.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))
    (repo / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (repo / "CHANGELOG.md").write_text("## 0.1.0\n\n- Initial\n", encoding="utf-8")
    (repo / "artifact.txt").write_text("artifact\n", encoding="utf-8")
    git(repo, "add", "--", "VERSION", "CHANGELOG.md", "artifact.txt")
    git(repo, "commit", "-m", "chore: 准备发布")
    push_branch(repo, "origin", "main")
    profile = {
        "version_file": "VERSION",
        "changelog_file": "CHANGELOG.md",
        "changelog_section": "## {version}",
        "allowed_branches": ["main"],
        "tag_template": "v{version}",
        "remote": "origin",
        "required_assets": ["artifact.txt"],
        "draft": False,
        "prerelease": False,
        "regression": [["python3", "-c", "print('ok')"]],
        "build": [["python3", "-c", "print('build')"]],
    }
    readiness = check_readiness(
        repo,
        "0.1.0",
        profile=profile,
        regression=[["python3", "-c", "print('ok')"]],
        build=[["python3", "-c", "print('build')"]],
    )
    assert readiness["ready"] is True
    with pytest.raises(ReleaseError, match="Tag"):
        create_github_release(
            repo,
            "0.1.0",
            repository="owner/repo",
            remote="origin",
            notes="notes",
            title="v0.1.0",
            draft=False,
            prerelease=False,
            assets=[],
            asset_checksums={},
        )

    git(repo, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
    git(repo, "push", "origin", "refs/tags/v0.1.0")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log = tmp_path / "gh.json"
    created = tmp_path / "release-created"
    gh = fake_bin / "gh"
    gh.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "open(os.environ['FAKE_GH_LOG'], 'a').write(json.dumps(args) + '\\n')\n"
        "if args[:1] == ['api'] and '/git/ref/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'tag','sha':os.environ['FAKE_TAG_OBJECT']}}))\n"
        "elif args[:1] == ['api'] and '/git/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'commit','sha':os.environ['FAKE_RELEASE_TARGET']}}))\n"
        "elif args[:2] == ['release', 'create']:\n"
        " open(os.environ['FAKE_RELEASE_CREATED'], 'w').write('yes')\n"
        "elif args[:2] == ['release', 'view'] and not os.path.exists(os.environ['FAKE_RELEASE_CREATED']):\n"
        " print('release not found', file=sys.stderr)\n"
        " raise SystemExit(1)\n"
        "elif args[:2] == ['release', 'view']:\n"
        " print(json.dumps({'tagName':'v0.1.0','name':'v0.1.0','body':'notes',"
        "'isDraft':False,'isPrerelease':False,'url':'https://github.com/owner/repo/releases/tag/v0.1.0',"
        "'targetCommitish':os.environ['FAKE_RELEASE_TARGET'],'assets':[]}))\n",
        encoding="utf-8",
    )
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_GH_LOG", str(log))
    monkeypatch.setenv("FAKE_RELEASE_CREATED", str(created))
    monkeypatch.setenv(
        "FAKE_TAG_OBJECT",
        git(repo, "rev-parse", "refs/tags/v0.1.0"),
    )
    monkeypatch.setenv("FAKE_RELEASE_TARGET", git(repo, "rev-parse", "HEAD"))
    monkeypatch.setenv("GH_HOST", "attacker.invalid")
    monkeypatch.setenv("GH_REPO", "attacker/redirect")
    result = create_github_release(
        repo,
        "0.1.0",
        repository="owner/repo",
        remote="origin",
        notes="notes",
        title="v0.1.0",
        draft=False,
        prerelease=False,
        assets=[],
        asset_checksums={},
    )
    assert result["verified_tag"] is True
    assert result["repository"] == "owner/repo"
    assert result["hostname"] == "github.com"
    calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    release_calls = [argv for argv in calls if argv[:1] == ["release"]]
    assert "--verify-tag" in release_calls[1]
    assert all(
        "--repo" in argv and argv[argv.index("--repo") + 1] == "owner/repo"
        for argv in release_calls
    )


def test_release_profile_loads_from_project_toml(tmp_path: Path) -> None:
    profile_path = tmp_path / ".auto-git.toml"
    profile_path.write_text(
        "[release]\n"
        'version_file = "VERSION"\n'
        'changelog_file = "CHANGELOG.md"\n'
        'changelog_section = "## {version}"\n'
        'allowed_branches = ["main"]\n'
        'tag_template = "v{version}"\n'
        'remote = "origin"\n'
        'required_assets = ["dist/skill.zip"]\n'
        "draft = false\n"
        "prerelease = false\n"
        'regression = [["python3", "-m", "pytest", "-q"]]\n'
        'build = [["python3", "scripts/build.py"]]\n',
        encoding="utf-8",
    )
    profile = load_release_profile(profile_path)
    assert profile["allowed_branches"] == ["main"]
    assert profile["regression"][0][:3] == ["python3", "-m", "pytest"]


def test_repository_release_profile_declares_all_p0_gates() -> None:
    root = Path(__file__).resolve().parents[2]
    profile = load_release_profile(root / ".auto-git.toml")
    assert profile["allowed_branches"] == ["main"]
    assert profile["remote"] == "origin"
    assert {"SKILL.md", "skill.contract.yaml", "README.md", "README.en.md"} <= set(
        profile["required_assets"]
    )
    assert profile["regression"]
    assert profile["build"]


def test_release_readiness_requires_profile_branch_upstream_assets_and_no_tag(
    repo: Path,
    tmp_path: Path,
) -> None:
    (repo / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (repo / "CHANGELOG.md").write_text("## 0.1.0\n", encoding="utf-8")
    git(repo, "add", "--", "VERSION", "CHANGELOG.md")
    git(repo, "commit", "-m", "chore: 准备发布")
    missing_profile = check_readiness(
        repo,
        "0.1.0",
        profile=None,
        regression=[],
        build=[],
    )
    assert missing_profile["ready"] is False
    assert any("profile" in item for item in missing_profile["problems"])

    profile = {
        "version_file": "VERSION",
        "changelog_file": "CHANGELOG.md",
        "changelog_section": "## {version}",
        "allowed_branches": ["release"],
        "tag_template": "v{version}",
        "remote": "origin",
        "required_assets": ["missing.zip"],
        "draft": False,
        "prerelease": False,
        "regression": [],
        "build": [],
    }
    result = check_readiness(
        repo,
        "0.1.0",
        profile=profile,
        regression=[],
        build=[],
    )
    assert result["ready"] is False
    assert any("分支" in item for item in result["problems"])
    assert any("asset" in item for item in result["problems"])
    assert any("upstream" in item or "Remote" in item for item in result["problems"])

    bare = tmp_path / "release.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))
    push_branch(repo, "origin", "main")
    profile["allowed_branches"] = ["main"]
    profile["required_assets"] = ["README.md"]
    git(repo, "tag", "-a", "v0.1.0", "-m", "conflict")
    conflict = check_readiness(
        repo,
        "0.1.0",
        profile=profile,
        regression=[],
        build=[],
    )
    assert conflict["ready"] is False
    assert any("Tag" in item for item in conflict["problems"])


def test_release_resume_detects_pushed_tag(
    repo: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    bare = tmp_path / "release.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))
    git(repo, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
    git(repo, "push", "origin", "refs/tags/v0.1.0")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    gh = fake_bin / "gh"
    gh.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "if args[:1] == ['api'] and '/git/ref/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'tag','sha':os.environ['TAG_OBJECT']}}))\n"
        "elif args[:1] == ['api'] and '/git/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'commit','sha':os.environ['TAG_TARGET']}}))\n"
        "else:\n"
        " print('release not found', file=sys.stderr)\n"
        " raise SystemExit(1)\n",
        encoding="utf-8",
    )
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("TAG_OBJECT", git(repo, "rev-parse", "refs/tags/v0.1.0"))
    monkeypatch.setenv("TAG_TARGET", git(repo, "rev-parse", "refs/tags/v0.1.0^{}"))
    status = release_status(
        repo,
        "0.1.0",
        remote="origin",
        repository="owner/repo",
        expected_release={
            "title": "v0.1.0",
            "notes": "notes",
            "draft": False,
            "prerelease": False,
            "assets": [],
            "asset_checksums": {},
        },
    )
    assert status["local_tag"] is True
    assert status["remote_tag"] is True
    assert status["next_stage"] == "github_release"
    assert status["github_release"] is False


def test_release_resume_returns_completed_for_exact_existing_release(
    repo: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    bare = tmp_path / "release.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))
    git(repo, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
    git(repo, "push", "origin", "refs/tags/v0.1.0")
    target = git(repo, "rev-parse", "HEAD")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    gh = fake_bin / "gh"
    gh.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "if args[:1] == ['api'] and '/git/ref/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'tag','sha':os.environ['TAG_OBJECT']}}))\n"
        "elif args[:1] == ['api'] and '/git/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'commit','sha':os.environ['FAKE_RELEASE_TARGET']}}))\n"
        "else:\n"
        " print(json.dumps({'tagName':'v0.1.0','name':'v0.1.0','body':'notes',"
        "'isDraft':False,'isPrerelease':False,"
        "'url':'https://github.com/owner/repo/releases/tag/v0.1.0',"
        "'targetCommitish':os.environ['FAKE_RELEASE_TARGET'],'assets':[]}))\n",
        encoding="utf-8",
    )
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_RELEASE_TARGET", target)
    monkeypatch.setenv("TAG_OBJECT", git(repo, "rev-parse", "refs/tags/v0.1.0"))
    expected = {
        "title": "v0.1.0",
        "notes": "notes",
        "draft": False,
        "prerelease": False,
        "assets": [],
        "asset_checksums": {},
    }
    status = release_status(
        repo,
        "0.1.0",
        remote="origin",
        repository="owner/repo",
        expected_release=expected,
    )
    assert status["next_stage"] == "completed"
    assert status["release_status"] == "already_verified"
    assert status["github_release"] is True

    conflict = dict(expected, notes="different")
    with pytest.raises(ReleaseError, match="冲突"):
        release_status(
            repo,
            "0.1.0",
            remote="origin",
            repository="owner/repo",
            expected_release=conflict,
        )


def test_release_resume_rejects_provider_tag_oid_mismatch(
    repo: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    bare = tmp_path / "release.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))
    git(repo, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
    git(repo, "push", "origin", "refs/tags/v0.1.0")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    gh = fake_bin / "gh"
    gh.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "args = sys.argv[1:]\n"
        "if args[:1] == ['api'] and '/git/ref/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'tag','sha':'f' * 40}}))\n"
        "elif args[:1] == ['api'] and '/git/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'commit','sha':'e' * 40}}))\n"
        "else:\n"
        " print('release not found', file=sys.stderr)\n"
        " raise SystemExit(1)\n",
        encoding="utf-8",
    )
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    with pytest.raises(ReleaseError, match="GitHub.*Tag.*不一致"):
        release_status(
            repo,
            "0.1.0",
            remote="origin",
            repository="owner/repo",
            expected_release={
                "title": "v0.1.0",
                "notes": "notes",
                "draft": False,
                "prerelease": False,
                "assets": [],
                "asset_checksums": {},
            },
        )


def test_release_resume_rejects_same_name_asset_with_wrong_digest(
    repo: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    bare = tmp_path / "release.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))
    git(repo, "tag", "-a", "v0.1.0", "-m", "v0.1.0")
    git(repo, "push", "origin", "refs/tags/v0.1.0")
    local_object = git(repo, "rev-parse", "refs/tags/v0.1.0")
    local_target = git(repo, "rev-parse", "refs/tags/v0.1.0^{}")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    gh = fake_bin / "gh"
    gh.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os\n"
        "args = __import__('sys').argv[1:]\n"
        "if args[:1] == ['api'] and '/git/ref/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'tag','sha':os.environ['TAG_OBJECT']}}))\n"
        "elif args[:1] == ['api'] and '/git/tags/' in args[1]:\n"
        " print(json.dumps({'object':{'type':'commit','sha':os.environ['TAG_TARGET']}}))\n"
        "else:\n"
        " print(json.dumps({'tagName':'v0.1.0','name':'v0.1.0','body':'notes',"
        "'isDraft':False,'isPrerelease':False,"
        "'url':'https://github.com/owner/repo/releases/tag/v0.1.0',"
        "'targetCommitish':os.environ['TAG_TARGET'],"
        "'assets':[{'name':'artifact.zip','digest':'sha256:' + '0' * 64}]}))\n",
        encoding="utf-8",
    )
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("TAG_OBJECT", local_object)
    monkeypatch.setenv("TAG_TARGET", local_target)
    with pytest.raises(ReleaseError, match="冲突"):
        release_status(
            repo,
            "0.1.0",
            remote="origin",
            repository="owner/repo",
            expected_release={
                "title": "v0.1.0",
                "notes": "notes",
                "draft": False,
                "prerelease": False,
                "assets": ["artifact.zip"],
                "asset_checksums": {"artifact.zip": "1" * 64},
            },
        )


def test_release_resume_blocks_when_remote_cannot_be_read(
    repo: Path,
    tmp_path: Path,
) -> None:
    connect_remote(repo, "origin", str(tmp_path / "missing.git"))
    with pytest.raises(ReleaseError, match="无法读取"):
        release_status(repo, "0.1.0", remote="origin")


def test_release_resume_rejects_lightweight_or_mismatched_remote_tag(
    repo: Path,
    tmp_path: Path,
) -> None:
    bare = tmp_path / "release.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))

    git(repo, "tag", "v0.1.0")
    git(repo, "push", "origin", "refs/tags/v0.1.0")
    with pytest.raises(ReleaseError, match="annotated"):
        release_status(repo, "0.1.0", remote="origin")

    git(repo, "tag", "-d", "v0.1.0")
    git(repo, "tag", "-a", "v0.1.0", "-m", "local")
    with pytest.raises(ReleaseError, match="不一致|annotated"):
        release_status(repo, "0.1.0", remote="origin")


def test_release_resume_rejects_different_tag_object_with_same_target(
    repo: Path,
    tmp_path: Path,
) -> None:
    bare = tmp_path / "release.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))
    git(repo, "tag", "-a", "remote-tag", "-m", "remote")
    git(repo, "push", "origin", "refs/tags/remote-tag:refs/tags/v0.1.0")
    git(repo, "tag", "-a", "v0.1.0", "-m", "local")
    with pytest.raises(ReleaseError, match="不一致"):
        release_status(repo, "0.1.0", remote="origin")


def test_operation_record_verifies_push_tag_and_tag_push_drift(
    repo: Path,
    tmp_path: Path,
) -> None:
    bare = tmp_path / "records.git"
    bare.mkdir()
    git(bare, "init", "--bare")
    connect_remote(repo, "origin", str(bare))

    push_plan = create_plan(
        "push",
        repo,
        {"remote": "origin", "branch": "main"},
    )
    push_record = apply_plan(
        push_plan,
        approval=push_plan["plan_hash"],
        state_home=tmp_path / "state",
    )
    assert verify_record(push_record)["verified"] is True
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    git(repo, "add", "--", "later.txt")
    git(repo, "commit", "-m", "feat: later")
    git(repo, "push", "origin", "main")
    assert verify_record(push_record)["verified"] is False

    tag_plan = create_plan("tag", repo, {"tag": "v0.1.0"})
    tag_record = apply_plan(
        tag_plan,
        approval=tag_plan["plan_hash"],
        state_home=tmp_path / "state",
    )
    assert verify_record(tag_record)["verified"] is True
    git(repo, "tag", "-f", "v0.1.0", "HEAD~1")
    assert verify_record(tag_record)["verified"] is False

    annotated_plan = create_plan("tag", repo, {"tag": "v0.2.0"})
    apply_plan(
        annotated_plan,
        approval=annotated_plan["plan_hash"],
        state_home=tmp_path / "state",
    )
    push_tag_plan = create_plan(
        "push_tag",
        repo,
        {"remote": "origin", "tag": "v0.2.0"},
    )
    push_tag_record = apply_plan(
        push_tag_plan,
        approval=push_tag_plan["plan_hash"],
        state_home=tmp_path / "state",
    )
    assert verify_record(push_tag_record)["verified"] is True
    git(repo, "push", "origin", ":refs/tags/v0.2.0")
    assert verify_record(push_tag_record)["verified"] is False


def test_verify_record_returns_unknown_for_unsupported_action(repo: Path) -> None:
    result = verify_record(
        {
            "schema_version": "1",
            "repo": str(repo),
            "action": "future_action",
            "status": "succeeded",
            "details": {},
        }
    )
    assert result["verified"] is None
    assert result["verification_status"] == "unknown"
