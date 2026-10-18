"""依赖安装计划；0.1.0 不自动执行 root/admin 安装。"""

from __future__ import annotations

import platform
from typing import Any


def dependency_plan(dependency: str, *, system: str | None = None) -> dict[str, Any]:
    normalized = (system or platform.system()).lower()
    if dependency not in {"git", "gh"}:
        raise ValueError("只支持 git 或 gh")
    guidance = {
        ("darwin", "git"): ["xcode-select", "--install"],
        ("darwin", "gh"): ["brew", "install", "gh"],
        ("linux", "git"): ["使用系统包管理器安装 git"],
        ("linux", "gh"): ["按 GitHub CLI 官方仓库安装 gh"],
        ("windows", "git"): ["winget", "install", "--id", "Git.Git"],
        ("windows", "gh"): ["winget", "install", "--id", "GitHub.cli"],
    }.get((normalized, dependency), ["打开官方安装指南"])
    return {
        "schema_version": "1",
        "dependency": dependency,
        "system": normalized,
        "guidance_argv_or_steps": guidance,
        "requires_approval": True,
        "automatic_root_install": False,
        "verify_argv": [dependency, "--version"],
    }


def skill_lifecycle_plan(
    action: str,
    *,
    scope: str,
    source: str,
    target: str,
) -> dict[str, Any]:
    """生成安装、升级或卸载预览，不执行宿主或 Global 写入。"""
    if action not in {"install", "upgrade", "uninstall"}:
        raise ValueError("action 必须是 install/upgrade/uninstall")
    if scope not in {"project", "profile", "global"}:
        raise ValueError("scope 必须是 project/profile/global")
    return {
        "schema_version": "1",
        "action": action,
        "scope": scope,
        "source": source,
        "target": target,
        "requires_approval": True,
        "requires_global_approval": scope == "global",
        "automatic_global_install": False,
        "ownership_and_fingerprint_required": action in {"upgrade", "uninstall"},
    }
