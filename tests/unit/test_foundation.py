"""版本化 JSON、运行器、状态与脱敏的单元测试。"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import auto_git.release as release_module
import auto_git.verification as verification_module
from auto_git.redaction import redact
from auto_git.runner import CommandError, run
from auto_git.schema import canonical_json, hash_payload
from auto_git.state import RepositoryLock, atomic_write_json, read_json


def test_canonical_hash_ignores_mapping_order() -> None:
    left = {"b": 2, "a": ["中", 1]}
    right = {"a": ["中", 1], "b": 2}
    assert canonical_json(left) == canonical_json(right)
    assert hash_payload(left) == hash_payload(right)


def test_runner_uses_argv_and_reports_failure(tmp_path: Path) -> None:
    result = run(["python3", "-c", "print('ok')"], cwd=tmp_path)
    assert result.stdout.strip() == "ok"
    with pytest.raises(CommandError) as caught:
        run(["python3", "-c", "raise SystemExit(7)"], cwd=tmp_path)
    assert caught.value.returncode == 7


def test_atomic_json_and_repository_lock(tmp_path: Path) -> None:
    target = tmp_path / "state" / "record.json"
    atomic_write_json(target, {"status": "ok"})
    assert read_json(target) == {"status": "ok"}
    lock_path = tmp_path / "repo.lock"
    with RepositoryLock(lock_path, action="stage_commit", repo=tmp_path):
        metadata = json.loads(lock_path.read_text(encoding="utf-8"))
        assert metadata["pid"] == os.getpid()
        assert metadata["action"] == "stage_commit"
        assert metadata["repo"] == str(tmp_path)
        assert metadata["started_at"]
        with pytest.raises(RuntimeError, match="锁"):
            with RepositoryLock(lock_path):
                pass


def test_repository_lock_reports_stale_owner_without_deleting_it(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "repo.lock"
    lock_path.write_text(
        json.dumps(
            {
                "pid": 999_999_999,
                "action": "push",
                "repo": str(tmp_path),
                "started_at": "2000-01-01T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="stale.*人工"):
        with RepositoryLock(lock_path):
            pass
    assert lock_path.exists()


def test_redaction_hides_credentials() -> None:
    prefix = "gh" + "p_"
    value = "authorization: Bearer " + prefix + "A" * 30
    assert prefix not in redact(value)
    assert "[redacted]" in redact(value)


def test_github_release_verifier_rejects_malformed_checksums_before_io(
    repo: Path,
    monkeypatch,
) -> None:
    def unexpected_io(*_args, **_kwargs):
        raise AssertionError("malformed record should fail before provider IO")

    monkeypatch.setattr(release_module, "_local_tag_facts", unexpected_io)
    monkeypatch.setattr(release_module, "_remote_tag_facts", unexpected_io)
    monkeypatch.setattr(release_module, "_github_tag_facts", unexpected_io)
    assert (
        verification_module._verify_github_release(
            repo,
            {
                "repository": "owner/repo",
                "asset_checksums": ["not", "a", "mapping"],
            },
        )
        is False
    )


@pytest.mark.parametrize(
    "record",
    [
        {"repo": None, "action": "stage_commit", "details": {}},
        ["not", "a", "record"],
    ],
)
def test_verify_record_fails_closed_for_malformed_record(record: object) -> None:
    result = verification_module.verify_record(record)
    assert result["verified"] is False
    assert result["verification_status"] == "drifted"
