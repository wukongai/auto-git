"""远程事实必须先预览，再按同一目标和提交批准执行。"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest

from auto_git.remote import RemoteError, connect_remote, push_branch
from auto_git.runner import CommandError, CommandResult
from conftest import git


def _api():
    """缺少预检模块时给出明确的 RED 原因。"""
    assert importlib.util.find_spec("auto_git.remote_preflight"), "缺少远程批准事实预检"
    return importlib.import_module("auto_git.remote_preflight")


def _bare(tmp_path: Path, name: str = "remote.git") -> Path:
    """仅创建本机临时 bare 仓库。"""
    path = tmp_path / name
    git(tmp_path, "init", "--bare", str(path))
    return path


def _commit(repo: Path, name: str = "next.md") -> str:
    """为计划漂移测试追加一份明确文件。"""
    (repo / name).write_text(name + "\n", encoding="utf-8")
    git(repo, "add", "--", name)
    git(repo, "commit", "-m", "追加受控提交")
    return git(repo, "rev-parse", "HEAD")


def _connect(repo: Path, bare: Path) -> None:
    """夹具连接只指向本地临时目录。"""
    git(repo, "remote", "add", "origin", str(bare))


def _advance(repo: Path, bare: Path, tmp_path: Path) -> str:
    """模拟另一个本地参与者在预览后推进远端。"""
    peer = tmp_path / "peer"
    git(tmp_path, "clone", "--branch", "main", str(bare), str(peer))
    git(peer, "config", "user.name", "另一参与者")
    git(peer, "config", "user.email", "peer@example.invalid")
    oid = _commit(peer, "peer.md")
    git(peer, "push", "origin", "main")
    return oid


def test_push_snapshot_fixes_full_commit_list_and_first_push(repo: Path, tmp_path: Path):
    """首次 Push 应展示全部历史而非零 ahead。"""
    api = _api()
    bare = _bare(tmp_path)
    _connect(repo, bare)
    first = git(repo, "rev-parse", "HEAD")
    second = _commit(repo)
    snapshot = api.build_push_preflight(repo, "origin", "main")
    assert snapshot["local_head"] == second
    assert snapshot["remote_oid"] is None
    assert snapshot["commits"] == [first, second]
    assert snapshot["ahead"] == 2 and snapshot["behind"] == 0
    assert snapshot["url_identity"] == f"file://{bare}"
    result = push_branch(repo, "origin", "main", expected=snapshot)
    assert result["verified"] is True and result["remote"] == second
    assert result["upstream"] == "origin/main"
    assert result["url_identity"] == snapshot["url_identity"]


def test_push_snapshot_lists_only_new_commits(repo: Path, tmp_path: Path):
    """已有远端的预览只列出尚未发送的完整 OID。"""
    api = _api()
    bare = _bare(tmp_path)
    _connect(repo, bare)
    git(repo, "push", "-u", "origin", "main")
    previous = git(repo, "rev-parse", "HEAD")
    current = _commit(repo)
    snapshot = api.build_push_preflight(repo, "origin", "main")
    assert snapshot["remote_oid"] == previous
    assert snapshot["commits"] == [current]
    api.validate_push_preflight(repo, snapshot)


def test_push_snapshot_blocks_initial_head(repo: Path, tmp_path: Path):
    """未提交的初始仓库无法批准 Push，但可用于连接预览。"""
    api = _api()
    empty = tmp_path / "initial"
    empty.mkdir()
    git(empty, "init", "-b", "main")
    bare = _bare(tmp_path)
    _connect(empty, bare)
    with pytest.raises(RemoteError, match="HEAD|提交"):
        api.build_push_preflight(empty, "origin", "main")
    assert api.build_connection_preflight(empty, "origin", str(bare))["local_head"] is None


def test_push_blocks_remote_advance_after_preview(repo: Path, tmp_path: Path):
    """计划后远端推进必须要求重新预览且不产生 Push。"""
    api = _api()
    bare = _bare(tmp_path)
    _connect(repo, bare)
    git(repo, "push", "-u", "origin", "main")
    _commit(repo)
    snapshot = api.build_push_preflight(repo, "origin", "main")
    remote_oid = _advance(repo, bare, tmp_path)
    with pytest.raises(RemoteError):
        push_branch(repo, "origin", "main", expected=snapshot)
    assert git(bare, "rev-parse", "refs/heads/main") == remote_oid


@pytest.mark.parametrize("field", ["url", "pushurl", "head", "branch"])
def test_push_rejects_changed_target_or_local_facts(repo: Path, tmp_path: Path, field: str):
    """URL、Push URL、HEAD 和分支都是同一批准的组成部分。"""
    api = _api()
    bare = _bare(tmp_path)
    other = _bare(tmp_path, "other.git")
    _connect(repo, bare)
    snapshot = api.build_push_preflight(repo, "origin", "main")
    if field == "url":
        git(repo, "remote", "set-url", "origin", str(other))
    elif field == "pushurl":
        git(repo, "config", "remote.origin.pushurl", str(other))
    elif field == "head":
        _commit(repo)
    else:
        git(repo, "switch", "-c", "other")
    with pytest.raises(RemoteError):
        push_branch(repo, "origin", "main", expected=snapshot)
    assert not git(bare, "for-each-ref")
    assert not git(other, "for-each-ref")


def test_push_fetch_failure_is_closed(repo: Path, tmp_path: Path):
    """不存在的本地目标模拟 fetch 失败，不使用旧缓存。"""
    api = _api()
    _connect(repo, tmp_path / "missing.git")
    with pytest.raises(RemoteError, match="fetch|读取|远端"):
        api.build_push_preflight(repo, "origin", "main")


def test_push_already_synced_never_calls_push(repo: Path, tmp_path: Path, monkeypatch):
    """同 OID 已同步只做读取，不重新写远端或配置。"""
    api = _api()
    bare = _bare(tmp_path)
    _connect(repo, bare)
    git(repo, "push", "-u", "origin", "main")
    snapshot = api.build_push_preflight(repo, "origin", "main")
    import auto_git.remote as module

    real_run = module.run

    def guarded(argv, **kwargs):
        """任何实际 Push 都表示幂等语义回归。"""
        assert argv[:2] != ["git", "push"], "已同步时不应 Push"
        return real_run(argv, **kwargs)

    monkeypatch.setattr(module, "run", guarded)
    result = push_branch(repo, "origin", "main", expected=snapshot)
    assert result["status"] == "already_synced"
    assert result["verified"] is True and result["commits"] == []
    assert result["url_identity"] == snapshot["url_identity"]


@pytest.mark.parametrize("wrong_upstream", [False, True])
def test_already_synced_requires_correct_upstream_without_writes(
    repo: Path, tmp_path: Path, monkeypatch, wrong_upstream: bool,
):
    """OID 相同不能代替上游合同，缺失或错误时单独提示配置。"""
    api = _api()
    bare = _bare(tmp_path)
    _connect(repo, bare)
    git(repo, "push", "origin", "main")
    if wrong_upstream:
        git(repo, "config", "branch.main.remote", ".")
        git(repo, "config", "branch.main.merge", "refs/heads/main")
    snapshot = api.build_push_preflight(repo, "origin", "main")
    before_config = git(repo, "config", "--local", "--list")
    before_refs = git(bare, "for-each-ref")
    import auto_git.remote as module

    real_run = module.run

    def guarded(argv, **kwargs):
        """无动作路径禁止借机写远端或补配本地上游。"""
        assert argv[:2] != ["git", "push"]
        assert not any(arg.startswith("--set-upstream") for arg in argv)
        return real_run(argv, **kwargs)

    monkeypatch.setattr(module, "run", guarded)
    with pytest.raises(RemoteError, match="单独.*upstream|单独.*上游") as failure:
        push_branch(repo, "origin", "main", expected=snapshot)
    assert getattr(failure.value, "before_remote_write", False) is True
    assert git(repo, "config", "--local", "--list") == before_config
    assert git(bare, "for-each-ref") == before_refs


def test_connection_empty_preview_and_apply(repo: Path, tmp_path: Path):
    """空库预览不连接，批准后再写本地 Remote。"""
    api = _api()
    bare = _bare(tmp_path)
    snapshot = api.build_connection_preflight(repo, "origin", str(bare))
    assert snapshot["history"] == "empty" and snapshot["remote_refs"] == {}
    assert git(repo, "remote") == ""
    api.validate_connection_preflight(repo, snapshot)
    result = connect_remote(repo, "origin", str(bare), expected=snapshot)
    assert result["changed"] is True


@pytest.mark.parametrize("related", [True, False])
def test_connection_classifies_only_locally_provable_history(repo: Path, tmp_path: Path, related: bool):
    """已知共同历史与不能证明的远端历史不能混称安全。"""
    api = _api()
    bare = _bare(tmp_path)
    if related:
        git(repo, "push", str(bare), "main")
    else:
        unrelated = tmp_path / "unrelated"
        unrelated.mkdir()
        git(unrelated, "init", "-b", "main")
        git(unrelated, "config", "user.name", "独立作者")
        git(unrelated, "config", "user.email", "other@example.invalid")
        _commit(unrelated)
        git(unrelated, "push", str(bare), "main")
    snapshot = api.build_connection_preflight(repo, "origin", str(bare))
    assert snapshot["history"] == ("related" if related else "unknown")
    assert snapshot["remote_refs"]["refs/heads/main"]


def test_connection_existing_different_url_is_rejected(repo: Path, tmp_path: Path):
    """现有 Remote 不会被另一个预览地址替换。"""
    api = _api()
    bare = _bare(tmp_path)
    other = _bare(tmp_path, "other.git")
    _connect(repo, bare)
    with pytest.raises(RemoteError, match="不一致|不同"):
        api.build_connection_preflight(repo, "origin", str(other))


def test_connection_remote_change_invalidates_approval(repo: Path, tmp_path: Path):
    """预览为空后有人发布了历史，连接前必须重新预览。"""
    api = _api()
    bare = _bare(tmp_path)
    snapshot = api.build_connection_preflight(repo, "origin", str(bare))
    git(repo, "push", str(bare), "main")
    with pytest.raises(RemoteError, match="漂移|变化|预览"):
        connect_remote(repo, "origin", str(bare), expected=snapshot)
    assert git(repo, "remote") == ""


def test_connection_read_failure_and_credentials_fail_closed(repo: Path, tmp_path: Path, monkeypatch):
    """网络故障及含凭证目标均不能形成可批准事实。"""
    api = _api()
    bare = _bare(tmp_path)
    with pytest.raises(RemoteError, match="凭证"):
        api.build_connection_preflight(repo, "origin", "https://user:secret@example.invalid/repo.git")
    real_run = api.run

    def failed_read(argv, **kwargs):
        """仅模拟 ls-remote 断线，其余本地事实正常。"""
        if argv[:2] == ["git", "ls-remote"]:
            raise CommandError(CommandResult(tuple(argv), 1, "", "network unavailable"))
        return real_run(argv, **kwargs)

    monkeypatch.setattr(api, "run", failed_read)
    with pytest.raises(RemoteError, match="读取|远端"):
        api.build_connection_preflight(repo, "origin", str(bare))
