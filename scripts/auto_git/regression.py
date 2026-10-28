"""运行计划中显式声明的回归命令。"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .runner import CommandError, run


class RegressionError(RuntimeError):
    """检查失败时保留无原始输出的命令结果，供执行回执记录。"""

    def __init__(self, message: str, results: list[dict[str, object]] | None = None):
        super().__init__(message)
        self.results = results or []


def run_regression(
    commands: Sequence[Sequence[str]],
    repo: Path,
) -> list[dict[str, object]]:
    if not commands:
        raise RegressionError("至少需要一条回归命令，空列表不代表检查通过")
    results = []
    for argv in commands:
        if not argv:
            raise RegressionError("回归命令不能为空")
        try:
            result = run(list(argv), cwd=repo)
        except CommandError as exc:
            results.append({"argv": list(argv), "returncode": exc.returncode})
            raise RegressionError(f"回归失败：{argv[0]}", results) from exc
        results.append({"argv": list(argv), "returncode": result.returncode})
    return results
