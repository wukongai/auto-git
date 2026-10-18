"""版本化 JSON 与不可变 hash。"""

from __future__ import annotations

import hashlib
import json
from typing import Any


SCHEMA_VERSION = "1"


def canonical_json(value: Any) -> str:
    """返回稳定、UTF-8 友好的 JSON 表示。"""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def hash_payload(value: Any) -> str:
    """计算 canonical JSON 的 SHA-256。"""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
