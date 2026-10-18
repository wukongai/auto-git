"""日志和错误输出脱敏。"""

from __future__ import annotations

import re


_PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)\S+"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)(?:token|password|secret)\s*[=:]\s*\S+"),
)


def redact(value: str) -> str:
    """删除常见凭证形态，但保留可定位的普通错误。"""
    result = value
    for pattern in _PATTERNS:
        result = pattern.sub("[redacted]", result)
    return result
