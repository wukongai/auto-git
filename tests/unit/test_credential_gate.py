"""在临时仓库验证真实提交hook，不接触真实凭证或远端。"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("kind", ["safe", "github", "openai", "private-key"])
def test_commit_gate_checks_all_patterns_without_disclosing_values(tmp_path, kind):
    """干净提交通过，各类合成凭证被阻断且不回显正文。"""
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, capture_output=True, text=True, check=False
        )

    assert git("init").returncode == 0
    assert git("config", "user.email", "fixture@example.invalid").returncode == 0
    assert git("config", "user.name", "测试夹具").returncode == 0
    assert git("config", "commit.gpgsign", "false").returncode == 0
    assert git("config", "core.hooksPath", ".git/hooks").returncode == 0
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("credential-lint.sh", "pre-commit.sh"):
        shutil.copy2(ROOT / "scripts" / name, scripts / name)
    (tmp_path / ".git/hooks/pre-commit").symlink_to("../../scripts/pre-commit.sh")
    values = {
        "safe": "普通文档内容",
        "github": "ghp_" + "A" * 36,
        "openai": "sk-" + "B" * 30,
        "private-key": "-----BEGIN " + "RSA PRIVATE KEY-----",
    }
    value = values[kind]
    (tmp_path / "note.txt").write_text(value + "\n")
    assert git("add", "--", "note.txt").returncode == 0
    result = git("commit", "-m", "测试提交门禁")
    output = result.stdout + result.stderr
    if kind == "safe":
        assert result.returncode == 0, output
    else:
        assert result.returncode != 0
        assert "疑似凭证" in output
        assert value not in output
