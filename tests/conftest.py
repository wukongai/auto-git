"""Auto Git 测试公共夹具。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def git(cwd: Path, *args: str, input_bytes: bytes | None = None) -> str:
    """在临时仓库运行 Git，失败时让测试直接显示 stderr。"""
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        input=input_bytes,
        capture_output=True,
        check=True,
    )
    return completed.stdout.decode("utf-8", errors="surrogateescape").strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "工作 项目"
    path.mkdir()
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Auto Git Test")
    git(path, "config", "user.email", "auto-git@example.invalid")
    (path / "README.md").write_text("# demo\n", encoding="utf-8")
    git(path, "add", "--", "README.md")
    git(path, "commit", "-m", "初始提交")
    return path
