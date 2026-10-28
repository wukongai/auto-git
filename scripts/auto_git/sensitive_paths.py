"""只按名称识别敏感路径；示例名称不能证明正文不含凭证。"""

from __future__ import annotations

from pathlib import Path


_EXAMPLE_NAMES = {".env.example", ".env.sample", ".env.template"}
_PRIVATE_NAMES = {
    ".netrc", ".npmrc", ".pypirc", "credentials", "id_rsa", "id_dsa",
    "id_ecdsa", "id_ed25519", "service-account.json", "service_account.json",
}
_PRIVATE_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".jks", ".keystore"}


def is_sensitive_path(value: str | Path) -> bool:
    """不访问文件系统，只用名称决定是否禁止读取正文和自动暂存。"""
    path = Path(value)
    name = path.name.lower()
    if any(part.lower() in {".ssh", ".aws", ".gnupg"} for part in path.parts):
        return True
    if name in _EXAMPLE_NAMES:
        return False
    return (
        name.startswith(".env") or name in _PRIVATE_NAMES
        or path.suffix.lower() in _PRIVATE_SUFFIXES
        or name.startswith(("credentials.", "secrets.", "secret.", "tokens.", "token."))
    )
