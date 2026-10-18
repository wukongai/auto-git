"""只接受 program + argv 的子进程运行器。"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .redaction import redact


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class CommandError(RuntimeError):
    """确定性命令失败。"""

    def __init__(self, result: CommandResult):
        self.result = result
        self.returncode = result.returncode
        super().__init__(
            f"命令失败({result.returncode}): {result.argv[0]}: "
            f"{redact(result.stderr).strip()}"
        )


def run(
    argv: Sequence[str],
    *,
    cwd: Path | str | None = None,
    input_bytes: bytes | None = None,
    timeout: float = 120,
    env: Mapping[str, str] | None = None,
    check: bool = True,
) -> CommandResult:
    """不经 shell 运行 argv，并统一返回 UTF-8/surrogateescape 文本。"""
    if not argv or not all(isinstance(item, str) and item for item in argv):
        raise ValueError("argv 必须是非空字符串序列")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        completed = subprocess.run(
            list(argv),
            cwd=cwd,
            input=input_bytes,
            capture_output=True,
            timeout=timeout,
            env=merged_env,
            shell=False,
            check=False,
        )
    except FileNotFoundError as exc:
        result = CommandResult(tuple(argv), 127, "", str(exc))
        raise CommandError(result) from exc
    except subprocess.TimeoutExpired as exc:
        result = CommandResult(
            tuple(argv),
            124,
            (exc.stdout or b"").decode("utf-8", errors="surrogateescape"),
            "命令超时",
        )
        raise CommandError(result) from exc
    result = CommandResult(
        tuple(argv),
        completed.returncode,
        completed.stdout.decode("utf-8", errors="surrogateescape"),
        completed.stderr.decode("utf-8", errors="surrogateescape"),
    )
    if check and result.returncode:
        raise CommandError(result)
    return result
