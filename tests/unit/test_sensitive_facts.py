"""只读事实可以报告敏感路径，不能打开其正文。"""

from pathlib import Path

from auto_git.git_facts import inspect_repo


def test_inspect_only_uses_metadata_for_sensitive_path(repo: Path, monkeypatch) -> None:
    """通过拦截Python打开调用，证明.env正文没有被读取。"""
    sensitive = repo / ".env"
    sensitive.write_text("fixture-value-without-real-credential\n")
    original = Path.open

    def guarded(path, *args, **kwargs):
        assert path != sensitive, "不得读取敏感正文"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    facts = inspect_repo(repo)
    assert any(item["path"] == ".env" for item in facts["changes"])
    assert len(facts["fingerprint"]) == 64
