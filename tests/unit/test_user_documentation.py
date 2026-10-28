"""面向用户的双语入口、操作手册与布丁发布边界测试。"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
README_ZH = ROOT / "README.md"
README_EN = ROOT / "README.en.md"
USER_MANUAL = ROOT / "docs" / "knowledge" / "users" / "guides" / "auto-git-user-manual.zh-CN.md"
INSTALL_REFERENCE = ROOT / "references" / "install.md"
RELEASE_REFERENCE = ROOT / "references" / "release.md"
SKILL_ENTRY = ROOT / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def body_without_frontmatter(text: str) -> str:
    normalized = text.replace("\r\n", "\n").lstrip("\ufeff")
    if normalized.startswith("---\n"):
        closing = normalized.find("\n---\n", 4)
        if closing != -1:
            normalized = normalized[closing + 5 :]
    return normalized.strip()


def test_bilingual_readmes_exist_and_link_to_each_other() -> None:
    zh = read(README_ZH)
    en = read(README_EN)

    assert "[中文](README.md)" in "\n".join(zh.splitlines()[:8])
    assert "[English](README.en.md)" in "\n".join(zh.splitlines()[:8])
    assert "[中文](README.md)" in "\n".join(en.splitlines()[:8])
    assert "[English](README.en.md)" in "\n".join(en.splitlines()[:8])


@pytest.mark.parametrize(
    "required",
    [
        "0.1.0",
        "npx skills add",
        "github.com/wukongai/auto-git",
        "Gitee",
        "-g",
        "codex",
        "claude-code",
        "skills update auto-git",
        "skills remove auto-git",
        "Commit",
        "Push",
        "Release",
        "docs/knowledge/users/guides/auto-git-user-manual.zh-CN.md",
    ],
)
def test_readmes_share_key_user_facts(required: str) -> None:
    assert required in read(README_ZH)
    assert required in read(README_EN)


def test_readmes_state_side_effect_boundaries() -> None:
    zh = read(README_ZH)
    en = read(README_EN)
    assert "不会在后台监控文件夹" in zh
    assert "不会自动 Commit 或 Push" in zh
    assert "does not watch folders in the background" in en
    assert "does not automatically Commit or Push" in en
    assert "install.sh" not in zh
    assert "install.ps1" not in zh
    assert "install.sh" not in en
    assert "install.ps1" not in en


def test_bootstrap_path_is_honest_about_git_prerequisite() -> None:
    zh = read(README_ZH)
    en = read(README_EN)
    manual = read(USER_MANUAL)
    install = read(INSTALL_REFERENCE)
    skill = read(SKILL_ENTRY)

    assert "先准备 Git，再安装 Auto Git" in zh
    assert "install Git before Auto Git" in en
    assert "Auto Git 还没有安装，不能先运行自己的 doctor" in manual
    assert "标准仓库型 Skills CLI 会通过 Git 获取 Auto Git" in install
    assert "无 Git 获取 Auto Git 时使用带 manifest 与 SHA-256 的 Release 归档" not in skill
    assert "首次自举由宿主 Agent" in skill


def test_user_manual_is_a_complete_user_playbook() -> None:
    manual = read(USER_MANUAL)
    required_sections = [
        "Auto Git 是什么",
        "安装 Auto Git",
        "第一次运行",
        "安装或检查 Git",
        "配置提交姓名和邮箱",
        "初始化或检查项目",
        "准备一次 Commit",
        "连接远程仓库",
        "第一次 Push",
        "后续 Push",
        "Tag 和 GitHub Release",
        "失败与恢复",
        "更新 Auto Git",
        "卸载 Auto Git",
        "常见问题",
        "如何判断成功",
    ]
    for section in required_sections:
        assert section in manual
    assert manual.count("> 帮我") >= 10
    assert "预期结果" in manual
    assert "遇到问题" in manual
    assert "训练营模式" not in manual


def test_public_user_docs_do_not_contain_pudding_metadata() -> None:
    public_docs = [README_ZH, README_EN, USER_MANUAL]
    forbidden = [
        "pudding_id:",
        "pudding_url:",
        "pudding_public_url:",
        "pudding_synced:",
        "aixiaoai.cloud/admin/",
    ]
    for path in public_docs:
        text = read(path)
        for marker in forbidden:
            assert marker not in text, f"{path.relative_to(ROOT)} 包含布丁私有元数据 {marker}"


def test_runtime_install_reference_uses_standard_skill_sources() -> None:
    install = read(INSTALL_REFERENCE)
    assert "npx skills add wukongai/auto-git" in install
    assert "GitHub 主源" in install
    assert "Gitee 镜像" in install
    assert "npx skills update auto-git" in install
    assert "npx skills remove auto-git" in install
    assert "GitHub Release 下载版本化 Skill 归档" not in install
    assert "先装 Skill Engineering" not in install


def test_installation_status_does_not_claim_unverified_live_availability() -> None:
    for path in (README_ZH, README_EN, USER_MANUAL, INSTALL_REFERENCE):
        text = read(path).lower()
        assert (
            "安装试用仍待验收" in text
            or "installation trial remains unverified" in text
        ), path.relative_to(ROOT)


def test_release_reference_exposes_dual_remote_postflight() -> None:
    release = read(RELEASE_REFERENCE)
    assert "verify-mirrors" in release
    assert "--remote origin --remote gitee" in release
    assert "branch OID" in release
    assert "annotated Tag target" in release


def test_claude_permissions_do_not_auto_allow_git_writes_or_generic_runtimes() -> None:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    allowed = settings["permissions"]["allow"]
    denied = settings["permissions"]["deny"]
    for dangerous_allow in (
        "Bash(git branch:*)",
        "Bash(git remote:*)",
        "Bash(git -C:*)",
        "Bash(git status:*)",
        "Bash(git diff:*)",
        "Bash(git show:*)",
        "Bash(git log:*)",
        "Bash(git ls-remote:*)",
        "Bash(git rev-parse:*)",
        "Bash(cat:*)",
        "Bash(rg:*)",
        "Bash(find:*)",
        "Bash(git add:*)",
        "Bash(git commit:*)",
        "Bash(curl:*)",
        "Bash(python3:*)",
        "Bash(python:*)",
        "Bash(node:*)",
    ):
        assert dangerous_allow not in allowed
    assert "Bash(git add .:*)" in denied
    assert "Bash(git add --all:*)" in denied
    assert "Bash(git branch --show-current)" in allowed
    assert "Bash(git remote -v)" in allowed
    assert "Read(//**)" not in allowed
    assert "Read(./**)" in allowed


def test_pudding_projection_matches_repository_manual_when_configured() -> None:
    projection_value = os.environ.get("AUTO_GIT_PUDDING_MANUAL")
    if not projection_value:
        pytest.skip("公开仓库环境未配置 OB 布丁发布副本")

    projection = Path(projection_value)
    assert projection.is_file()
    published = read(projection)
    assert re.search(
        r'^title: "Auto Git[^"]*用户手册[^"]*"$',
        published,
        re.MULTILINE,
    )
    assert re.search(r'^description: ".+"$', published, re.MULTILINE)
    assert re.search(r"^type: text$", published, re.MULTILINE)
    assert re.search(
        r'^source: "https://github\.com/wukongai/auto-git"$',
        published,
        re.MULTILINE,
    )
    assert body_without_frontmatter(published) == body_without_frontmatter(read(USER_MANUAL))
