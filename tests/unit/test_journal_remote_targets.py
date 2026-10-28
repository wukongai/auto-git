"""远程动作开始前必须保存可只读核验的批准目标与正文摘要。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from conftest import git
from auto_git.operation_journal import OperationJournal
from auto_git.runner import CommandError, CommandResult
from auto_git.verification import verify_record


TAG = "v0.2.0"
NOTES = "仅用于测试的私有发布正文，不应进入running记录"
NOTES_HASH = hashlib.sha256(NOTES.encode("utf-8")).hexdigest()
ASSET_HASH = hashlib.sha256(b"fixture artifact").hexdigest()


@pytest.fixture
def tagged_repo(repo: Path, tmp_path: Path) -> tuple[Path, str, str]:
    """只创建临时本地Tag和配置，不访问远端。"""
    git(repo, "tag", "-a", TAG, "-m", "测试版本")
    git(repo, "remote", "add", "origin", str(tmp_path / "remote.git"))
    return repo, git(repo, "rev-parse", f"refs/tags/{TAG}"), git(repo, "rev-parse", "HEAD")


def _plan(repo: Path, action: str, params: dict) -> dict:
    """日志单测使用完整目标身份，不触发真正的GitHub计划认证。"""
    return {
        "id": "journal-target-" + action, "action": action, "repo": str(repo),
        "plan_hash": "a" * 64, "precondition_fingerprint": "b" * 64,
        "params": params,
    }


def _start(plan: dict, tmp_path: Path) -> tuple[dict, str]:
    """实际持久化并读回running，防止只检查内存预期。"""
    journal = OperationJournal(plan, tmp_path / "state")
    journal.start()
    raw = journal.path.read_text(encoding="utf-8")
    record = json.loads(raw)
    assert record["status"] == "running"
    return record["details"], raw


def _release_params() -> dict:
    """批准参数保留附件来源路径，日志应转换为远端名称及摘要。"""
    return {
        "version": "0.2.0", "repository": "owner/demo", "remote": "origin",
        "title": "测试发布", "notes": NOTES, "draft": True, "prerelease": False,
        "assets": ["dist/package.zip"],
        "asset_checksums": {"dist/package.zip": ASSET_HASH},
        "authenticated_account": "owner", "git_protocol": "ssh", "hostname": "github.com",
    }


def test_push_tag_running_record_fixes_object_target_and_endpoint(tagged_repo, tmp_path: Path) -> None:
    """Push发生后断线，也能从记录找到当时批准的准确Tag和目标。"""
    repo, object_oid, target = tagged_repo
    details, _ = _start(_plan(repo, "push_tag", {"tag": TAG, "remote": "origin"}), tmp_path)
    assert details["remote"] == "origin"
    assert details["tag"] == TAG
    assert details["object"] == object_oid
    assert details["target"] == target
    assert details["url_identity"] == f"file://{tmp_path / 'remote.git'}"


def test_new_tag_running_record_fixes_target_without_inventing_object(repo: Path, tmp_path: Path) -> None:
    """新annotated对象尚未产生，先固定目标Commit并明确object未知。"""
    details, _ = _start(_plan(repo, "tag", {"tag": TAG}), tmp_path)
    assert details["tag"] == TAG
    assert details["target"] == git(repo, "rev-parse", "HEAD")
    assert details.get("object") is None


def test_github_create_running_record_fixes_approved_repository(repo: Path, tmp_path: Path) -> None:
    """仓库创建发生后无法回读时，记录仍保留账号、目标及可见性。"""
    params = {
        "name": "owner/demo", "visibility": "private", "hostname": "github.com",
        "authenticated_account": "owner", "git_protocol": "ssh",
    }
    details, _ = _start(_plan(repo, "github_repo_create", params), tmp_path)
    assert details["name"] == "owner/demo"
    assert details["visibility"] == "private"
    assert details["hostname"] == "github.com"
    assert details["url_identity"] == "https://github.com/owner/demo"
    assert details["authenticated_account"] == "owner"
    assert details["git_protocol"] == "ssh"


def test_github_release_running_record_fixes_target_metadata_and_body_hash(tagged_repo, tmp_path: Path) -> None:
    """恢复核验所需字段齐全，但running记录不保存发布正文。"""
    repo, object_oid, target = tagged_repo
    details, raw = _start(_plan(repo, "github_release", _release_params()), tmp_path)
    assert details["repository"] == "owner/demo"
    assert details["remote"] == "origin"
    assert details["tag"] == TAG
    assert details["hostname"] == "github.com"
    assert details["tag_object"] == details["provider_tag_object"] == object_oid
    assert details["target"] == details["provider_tag_target"] == target
    assert details["expected_branch"] == "main"
    assert details["title"] == "测试发布"
    assert details["draft"] is True and details["prerelease"] is False
    assert details["assets"] == ["package.zip"]
    assert details["asset_checksums"] == {"package.zip": ASSET_HASH}
    assert details["notes_sha256"] == NOTES_HASH
    assert "notes" not in details
    assert NOTES not in raw


def test_push_tag_read_failure_in_real_wrapper_is_unknown(tagged_repo, monkeypatch) -> None:
    """check=False的真实Tag读取包装层也必须区分断线与确定漂移。"""
    import auto_git.release as release
    repo, object_oid, target = tagged_repo
    original = release.run

    def unavailable(argv, **kwargs):
        """仅模拟远端读取失败，其他查询仍在本地真实执行。"""
        if "ls-remote" in argv:
            return CommandResult(tuple(argv), 128, "", "fixture network unavailable")
        return original(argv, **kwargs)

    monkeypatch.setattr(release, "run", unavailable)
    record = {"repo": str(repo), "action": "push_tag", "status": "unknown",
              "details": {"remote": "origin", "tag": TAG, "object": object_oid, "target": target}}
    result = verify_record(record)
    assert result["verified"] is None
    assert result["verification_status"] == "unknown"


def test_github_repository_network_failure_is_unknown(repo: Path, monkeypatch) -> None:
    """gh读取失败不能宣称已证明仓库属性不同。"""
    import auto_git.verification as verification

    def unavailable(argv, **_kwargs):
        """不运行真实gh，只返回读取失败。"""
        assert argv[:3] == ["gh", "repo", "view"]
        raise CommandError(CommandResult(tuple(argv), 128, "", "fixture network unavailable"))

    monkeypatch.setattr(verification, "run", unavailable)
    record = {"repo": str(repo), "action": "github_repo_create", "status": "unknown",
              "details": {"name": "owner/demo", "visibility": "private", "hostname": "github.com",
                          "url_identity": "https://github.com/owner/demo"}}
    result = verify_record(record)
    assert result["verified"] is None
    assert result["verification_status"] == "unknown"


def _release_record(repo: Path, object_oid: str, target: str) -> dict:
    """正文仅有hash的新记录，应仍可核对服务端正文。"""
    return {"repo": str(repo), "action": "github_release", "status": "unknown", "details": {
        "repository": "owner/demo", "remote": "origin", "tag": TAG,
        "tag_object": object_oid, "target": target, "provider_tag_object": object_oid,
        "provider_tag_target": target, "expected_branch": "main", "hostname": "github.com",
        "title": "测试发布", "notes_sha256": NOTES_HASH, "draft": True, "prerelease": False,
        "assets": ["package.zip"], "asset_checksums": {"package.zip": ASSET_HASH},
    }}


def _release_view(target: str) -> dict:
    """本地构造服务端只读响应，绝不连接GitHub。"""
    return {
        "tagName": TAG, "name": "测试发布", "body": NOTES, "isDraft": True,
        "isPrerelease": False, "url": f"https://github.com/owner/demo/releases/tag/{TAG}",
        "targetCommitish": target, "assets": [{"name": "package.zip", "digest": "sha256:" + ASSET_HASH}],
    }


@pytest.mark.parametrize("failure", ("remote_tag", "provider_tag", "release_view", None))
def test_github_release_reading_distinguishes_unknown_and_complete_match(
    tagged_repo, monkeypatch, failure: str | None,
) -> None:
    """三条读取通道断线均未知；完整响应可用正文hash重新认证。"""
    import auto_git.release as release
    import auto_git.verification as verification
    repo, object_oid, target = tagged_repo
    record = _release_record(repo, object_oid, target)
    original_run = release.run
    tag_facts = {"exists": True, "object": object_oid, "target": target}
    if failure != "remote_tag":
        monkeypatch.setattr(release, "_remote_tag_facts", lambda *_args: tag_facts)
    if failure != "provider_tag":
        monkeypatch.setattr(release, "_github_tag_facts", lambda *_args: tag_facts)

    def release_run(argv, **kwargs):
        """覆盖真实包装层的check=False失败，保留本地Git读取。"""
        if "ls-remote" in argv or argv[0] == "gh":
            return CommandResult(tuple(argv), 128, "", "fixture network unavailable")
        return original_run(argv, **kwargs)

    def view(argv, **_kwargs):
        """发布页面响应完全由本地fixture提供。"""
        assert argv[:3] == ["gh", "release", "view"]
        if failure == "release_view":
            raise CommandError(CommandResult(tuple(argv), 128, "", "fixture network unavailable"))
        return CommandResult(tuple(argv), 0, json.dumps(_release_view(target)), "")

    monkeypatch.setattr(release, "run", release_run)
    monkeypatch.setattr(verification, "run", view)
    result = verify_record(record)
    assert result["verified"] is (True if failure is None else None)
    assert result["verification_status"] == ("verified" if failure is None else "unknown")


@pytest.mark.parametrize("response", ("invalid-json", "different-visibility"))
def test_certain_invalid_provider_facts_remain_drifted(repo: Path, monkeypatch, response: str) -> None:
    """只有可证明的无效或不等事实归为漂移，不能把它也改成网络未知。"""
    import auto_git.verification as verification
    payload = "invalid fixture JSON" if response == "invalid-json" else json.dumps({
        "nameWithOwner": "owner/demo", "visibility": "PUBLIC", "url": "https://github.com/owner/demo",
    })
    monkeypatch.setattr(verification, "run", lambda argv, **_kwargs: CommandResult(tuple(argv), 0, payload, ""))
    result = verify_record({"repo": str(repo), "action": "github_repo_create", "details": {
        "name": "owner/demo", "visibility": "private", "hostname": "github.com",
        "url_identity": "https://github.com/owner/demo",
    }})
    assert result["verified"] is False
    assert result["verification_status"] == "drifted"
