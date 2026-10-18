"""环境 capability doctor。"""

from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path
from typing import Any

from .runner import run
from .schema import SCHEMA_VERSION


def _capability(program: str, version_argv: list[str]) -> dict[str, Any]:
    path = shutil.which(program)
    if not path:
        return {"available": False, "path": None, "version": None}
    result = run(version_argv, check=False)
    first_line = (result.stdout or result.stderr).splitlines()
    return {
        "available": result.returncode == 0,
        "path": path,
        "version": first_line[0] if first_line else None,
    }


def doctor(repo: Path | str) -> dict[str, Any]:
    path = Path(repo).expanduser().resolve()
    identity = {"name": None, "email": None, "complete": False}
    if shutil.which("git"):
        name = run(["git", "config", "--get", "user.name"], cwd=path, check=False)
        email = run(["git", "config", "--get", "user.email"], cwd=path, check=False)
        identity = {
            "name": name.stdout.strip() or None,
            "email": email.stdout.strip() or None,
            "complete": bool(name.stdout.strip() and email.stdout.strip()),
        }
    gh_auth = {"available": False, "authenticated": False}
    if shutil.which("gh"):
        auth = run(["gh", "auth", "status"], cwd=path, check=False)
        gh_auth = {
            "available": True,
            "authenticated": auth.returncode == 0,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "system": platform.system().lower(),
        "machine": platform.machine().lower(),
        "capabilities": {
            "python": {
                "available": sys.version_info >= (3, 11),
                "path": sys.executable,
                "version": platform.python_version(),
            },
            "git": _capability("git", ["git", "--version"]),
            "gh": _capability("gh", ["gh", "--version"]),
            "github_auth": gh_auth,
            "identity": identity,
        },
    }
