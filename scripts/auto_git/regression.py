"""运行计划中显式声明的回归命令。"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .runner import CommandError, run


class RegressionError(RuntimeError):
    pass


def run_regression(
    commands: Sequence[Sequence[str]],
    repo: Path,
) -> list[dict[str, object]]:
    results = []
    for argv in commands:
        if not argv:
            raise RegressionError("回归命令不能为空")
        try:
            result = run(list(argv), cwd=repo)
        except CommandError as exc:
            raise RegressionError(f"回归失败：{argv[0]}") from exc
        results.append({"argv": list(argv), "returncode": result.returncode})
    return results
