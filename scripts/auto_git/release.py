"""Release readiness 和 GitHub Release 独立阶段。"""

from __future__ import annotations

import json
import hashlib
import tomllib
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote

from .regression import RegressionError, run_regression
from .runner import CommandError, run


class ReleaseError(RuntimeError):
    pass


class ReleaseReadUnavailable(ReleaseError):
    """远程读取失败，不等于已读取到确定不匹配。"""

    verification_unavailable = True


def load_release_profile(path: Path) -> dict[str, Any]:
    """从项目 `.auto-git.toml` 读取显式 release profile。"""
    if not path.is_file():
        raise ReleaseError(f"release profile 不存在：{path}")
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ReleaseError("release profile TOML 无效") from exc
    profile = payload.get("release")
    if not isinstance(profile, dict):
        raise ReleaseError("release profile 缺少 [release]")
    return profile


def validate_tag_name(repo: Path, tag: str) -> str:
    """在 Tag 名称进入 Git/gh argv 前使用 Git 自己的 ref 规则校验。"""
    if not isinstance(tag, str) or not tag or tag.startswith("-"):
        raise ReleaseError("Tag 名称无效")
    check = run(
        ["git", "check-ref-format", f"refs/tags/{tag}"],
        cwd=repo,
        check=False,
    )
    if check.returncode:
        raise ReleaseError("Tag 名称无效")
    return tag


def _local_tag_facts(repo: Path, tag: str) -> dict[str, Any]:
    tag_ref = f"refs/tags/{tag}"
    exists = run(["git", "show-ref", "--verify", tag_ref], cwd=repo, check=False)
    if exists.returncode:
        return {"exists": False}
    tag_type = run(["git", "cat-file", "-t", tag_ref], cwd=repo).stdout.strip()
    if tag_type != "tag":
        raise ReleaseError(f"Tag {tag} 必须是 annotated Tag")
    return {
        "exists": True,
        "object": run(["git", "rev-parse", tag_ref], cwd=repo).stdout.strip(),
        "target": run(["git", "rev-parse", f"{tag_ref}^{{}}"], cwd=repo).stdout.strip(),
    }


def _remote_tag_facts(repo: Path, remote: str, tag: str, *, endpoint: str | None = None) -> dict[str, Any]:
    from .remote import validate_remote_name

    remote = validate_remote_name(repo, remote, require_configured=True)
    tag_ref = f"refs/tags/{tag}"
    peeled_ref = f"{tag_ref}^{{}}"
    result = run(
        ["git", "ls-remote", "--tags", "--", endpoint or remote, tag_ref, peeled_ref],
        cwd=repo,
        check=False,
    )
    if result.returncode:
        raise ReleaseReadUnavailable(f"无法读取 Remote {remote} 的 Release 状态")
    refs: dict[str, str] = {}
    for line in result.stdout.splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) == 2:
            refs[fields[1]] = fields[0]
    if not refs:
        return {"exists": False}
    if tag_ref not in refs or peeled_ref not in refs:
        raise ReleaseError(f"Remote {remote} 的 Tag {tag} 不是完整 annotated Tag")
    return {
        "exists": True,
        "object": refs[tag_ref],
        "target": refs[peeled_ref],
    }


def _relative_file(repo: Path, value: object, label: str) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    candidate = (repo / relative).resolve()
    try:
        candidate.relative_to(repo.resolve())
    except ValueError:
        return None
    return candidate


def check_readiness(
    repo: Path,
    version: str,
    *,
    profile: Mapping[str, Any] | None,
    regression: Sequence[Sequence[str]] | None,
    build: Sequence[Sequence[str]] | None,
) -> dict[str, object]:
    problems: list[str] = []
    required = {
        "version_file",
        "changelog_file",
        "changelog_section",
        "allowed_branches",
        "tag_template",
        "remote",
        "required_assets",
        "draft",
        "prerelease",
        "regression",
        "build",
    }
    if not isinstance(profile, Mapping):
        return {"ready": False, "problems": ["release profile 缺失"]}
    missing = sorted(required - set(profile))
    if missing:
        problems.append(f"release profile 缺少字段：{', '.join(missing)}")
    if not isinstance(profile.get("draft"), bool) or not isinstance(
        profile.get("prerelease"),
        bool,
    ):
        problems.append("release profile draft/prerelease 必须是布尔值")

    version_file = _relative_file(repo, profile.get("version_file"), "version")
    changelog = _relative_file(repo, profile.get("changelog_file"), "changelog")
    if version_file is None:
        problems.append("version_file 路径无效")
    if changelog is None:
        problems.append("changelog_file 路径无效")
    if (
        version_file is None
        or not version_file.is_file()
        or version_file.read_text(encoding="utf-8").strip() != version
    ):
        problems.append("VERSION 不匹配")
    section_template = profile.get("changelog_section")
    expected_section = (
        section_template.format(version=version)
        if isinstance(section_template, str)
        else ""
    )
    if (
        changelog is None
        or not changelog.is_file()
        or not expected_section
        or expected_section not in changelog.read_text(encoding="utf-8")
    ):
        problems.append("CHANGELOG 缺少版本")
    if run(["git", "status", "--porcelain"], cwd=repo).stdout.strip():
        problems.append("工作区不干净")

    branch = run(["git", "branch", "--show-current"], cwd=repo).stdout.strip()
    allowed = profile.get("allowed_branches")
    if not isinstance(allowed, list) or branch not in allowed:
        problems.append(f"当前分支 {branch or '(detached)'} 不在 release 允许分支")

    assets = profile.get("required_assets")
    if not isinstance(assets, list):
        problems.append("release profile required_assets 无效")
    else:
        for item in assets:
            asset = _relative_file(repo, item, "asset")
            if asset is None or not asset.is_file():
                problems.append(f"必需 asset 缺失或路径无效：{item}")

    remote_value = profile.get("remote")
    if not isinstance(remote_value, str):
        problems.append("release profile Remote 无效")
    else:
        try:
            from .remote import remote_facts, validate_remote_name

            remote = validate_remote_name(repo, remote_value, require_configured=True)
            facts = remote_facts(repo, remote, branch)
            if facts.get("behind", 0) or facts.get("diverged"):
                problems.append("release upstream 落后或分叉")
            upstream = run(
                [
                    "git",
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{upstream}",
                ],
                cwd=repo,
                check=False,
            ).stdout.strip()
            if upstream != f"{remote}/{branch}":
                problems.append("release upstream 缺失或不匹配")
            template = profile.get("tag_template")
            if not isinstance(template, str) or "{version}" not in template:
                problems.append("release tag_template 无效")
            else:
                tag = validate_tag_name(repo, template.format(version=version))
                try:
                    local_tag = _local_tag_facts(repo, tag)
                    remote_tag = _remote_tag_facts(repo, remote, tag)
                    if local_tag["exists"] or remote_tag["exists"]:
                        problems.append(f"同名 Tag {tag} 已存在")
                except ReleaseError as exc:
                    problems.append(str(exc))
        except (RuntimeError, ValueError) as exc:
            problems.append(f"release Remote/upstream 检查失败：{exc}")

    regression_commands = (
        regression if regression is not None else profile.get("regression")
    )
    build_commands = build if build is not None else profile.get("build")
    if not isinstance(regression_commands, list) or not isinstance(
        build_commands,
        list,
    ):
        problems.append("release profile regression/build 无效")
        regression_commands = []
        build_commands = []
    try:
        run_regression(regression_commands, repo)
        run_regression(build_commands, repo)
    except RegressionError as exc:
        problems.append(str(exc))
    return {"ready": not problems, "problems": problems}


_RELEASE_JSON_FIELDS = (
    "tagName,name,body,isDraft,isPrerelease,url,targetCommitish,assets"
)


def _read_github_release(
    repo: Path,
    repository: str,
    tag: str,
) -> dict[str, Any] | None:
    from .github import github_env

    viewed = run(
        [
            "gh",
            "release",
            "view",
            tag,
            "--repo",
            repository,
            "--json",
            _RELEASE_JSON_FIELDS,
        ],
        cwd=repo,
        env=github_env(repository),
        check=False,
    )
    if viewed.returncode:
        diagnostic = viewed.stderr.lower()
        if "release not found" in diagnostic or "no release found" in diagnostic:
            return None
        raise ReleaseError("无法读取明确 GitHub 仓库的 Release 状态")
    try:
        payload = json.loads(viewed.stdout)
    except json.JSONDecodeError as exc:
        raise ReleaseError("GitHub Release 状态 JSON 无效") from exc
    if not isinstance(payload, dict):
        raise ReleaseError("GitHub Release 状态不是对象")
    return payload


def _github_tag_facts(
    repo: Path,
    repository: str,
    tag: str,
) -> dict[str, str]:
    """从明确 GitHub 仓库回读 annotated Tag object 与 peeled target。"""
    from .github import GITHUB_HOSTNAME, github_env

    encoded_tag = quote(tag, safe="")
    reference = run(
        [
            "gh",
            "api",
            f"repos/{repository}/git/ref/tags/{encoded_tag}",
            "--hostname",
            GITHUB_HOSTNAME,
        ],
        cwd=repo,
        env=github_env(repository),
        check=False,
    )
    if reference.returncode:
        raise ReleaseReadUnavailable("无法读取明确 GitHub 仓库的 Tag ref")
    try:
        reference_payload = json.loads(reference.stdout)
        reference_object = reference_payload["object"]
        tag_object = reference_object["sha"]
        object_type = reference_object["type"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ReleaseError("GitHub Tag ref 状态无效") from exc
    if object_type != "tag" or not isinstance(tag_object, str) or not tag_object:
        raise ReleaseError("GitHub Tag 不是 annotated Tag")
    annotated = run(
        [
            "gh",
            "api",
            f"repos/{repository}/git/tags/{tag_object}",
            "--hostname",
            GITHUB_HOSTNAME,
        ],
        cwd=repo,
        env=github_env(repository),
        check=False,
    )
    if annotated.returncode:
        raise ReleaseReadUnavailable("无法读取明确 GitHub 仓库的 annotated Tag object")
    try:
        annotated_payload = json.loads(annotated.stdout)
        target_object = annotated_payload["object"]
        target = target_object["sha"]
        target_type = target_object["type"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ReleaseError("GitHub annotated Tag object 状态无效") from exc
    if target_type != "commit" or not isinstance(target, str) or not target:
        raise ReleaseError("GitHub annotated Tag target 不是 Commit")
    return {"object": tag_object, "target": target}


def _release_asset_names(payload: Mapping[str, Any]) -> list[str]:
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise ReleaseError("GitHub Release assets 状态无效")
    return sorted(
        item["name"]
        for item in assets
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    )


def _release_asset_digests(payload: Mapping[str, Any]) -> dict[str, str]:
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise ReleaseError("GitHub Release assets 状态无效")
    digests: dict[str, str] = {}
    for item in assets:
        if not isinstance(item, dict):
            raise ReleaseError("GitHub Release asset 状态无效")
        name = item.get("name")
        digest = item.get("digest")
        if not isinstance(name, str) or not isinstance(digest, str):
            raise ReleaseError("GitHub Release asset 缺少服务端 digest")
        if name in digests:
            raise ReleaseError("GitHub Release asset 名称重复")
        digests[name] = digest
    return digests


def _release_matches(
    payload: Mapping[str, Any],
    *,
    repository: str,
    tag: str,
    branch: str,
    target: object,
    expected: Mapping[str, Any],
) -> bool:
    url = payload.get("url")
    expected_assets = expected.get("assets")
    expected_checksums = expected.get("asset_checksums")
    expected_digests = (
        {
            name: f"sha256:{checksum}"
            for name, checksum in expected_checksums.items()
        }
        if isinstance(expected_checksums, Mapping)
        and all(
            isinstance(name, str) and isinstance(checksum, str)
            for name, checksum in expected_checksums.items()
        )
        else None
    )
    return (
        isinstance(expected_assets, list)
        and all(isinstance(item, str) for item in expected_assets)
        and expected_digests is not None
        and payload.get("tagName") == tag
        and payload.get("name") == expected.get("title")
        and payload.get("body") == expected.get("notes")
        and payload.get("isDraft") is expected.get("draft")
        and payload.get("isPrerelease") is expected.get("prerelease")
        and payload.get("targetCommitish") in {target, branch}
        and _release_asset_names(payload) == sorted(expected_assets)
        and _release_asset_digests(payload) == expected_digests
        and isinstance(url, str)
        and url.startswith(f"https://github.com/{repository}/releases/")
    )


def _release_details(
    *,
    repository: str,
    remote: str,
    tag: str,
    local: Mapping[str, Any],
    payload: Mapping[str, Any],
    expected: Mapping[str, Any],
    asset_checksums: Mapping[str, str],
    expected_account: str | None,
    expected_protocol: str | None,
    already_verified: bool,
    provider_tag: Mapping[str, str],
) -> dict[str, object]:
    from .github import GITHUB_HOSTNAME

    return {
        "tag": tag,
        "verified_tag": True,
        "remote": remote,
        "repository": repository,
        "hostname": GITHUB_HOSTNAME,
        "tag_object": local["object"],
        "target": local["target"],
        "provider_target": payload["targetCommitish"],
        "provider_tag_object": provider_tag["object"],
        "provider_tag_target": provider_tag["target"],
        "title": expected["title"],
        "notes": expected["notes"],
        "draft": expected["draft"],
        "prerelease": expected["prerelease"],
        "assets": sorted(expected["assets"]),
        "asset_checksums": dict(asset_checksums),
        "url": payload["url"],
        "authenticated_account": expected_account,
        "git_protocol": expected_protocol,
        "already_verified": already_verified,
    }


def create_github_release(
    repo: Path,
    version: str,
    *,
    repository: str,
    remote: str,
    notes: str,
    title: str,
    draft: bool,
    prerelease: bool,
    assets: Sequence[str],
    asset_checksums: Mapping[str, str],
    expected_account: str | None = None,
    expected_protocol: str | None = None,
) -> dict[str, object]:
    from .github import auth_status, github_env, validate_repository_name

    repository = validate_repository_name(repository)
    tag = validate_tag_name(repo, f"v{version}")
    if expected_account is not None or expected_protocol is not None:
        authentication = auth_status()
        if (
            not authentication["authenticated"]
            or authentication["account"] != expected_account
            or authentication["git_protocol"] != expected_protocol
        ):
            raise ReleaseError("GitHub 认证账号或协议已从计划事实漂移")
    asset_paths: list[Path] = []
    named_checksums: dict[str, str] = {}
    for value in assets:
        asset = _relative_file(repo, value, "asset")
        if asset is None or not asset.is_file():
            raise ReleaseError(f"Release asset 缺失或路径无效：{value}")
        checksum = hashlib.sha256(asset.read_bytes()).hexdigest()
        if asset_checksums.get(value) != checksum:
            raise ReleaseError(f"Release asset checksum 已漂移：{value}")
        if asset.name in named_checksums:
            raise ReleaseError(f"Release asset 文件名重复：{asset.name}")
        named_checksums[asset.name] = checksum
        asset_paths.append(asset)
    expected = {
        "title": title,
        "notes": notes,
        "draft": draft,
        "prerelease": prerelease,
        "assets": sorted(path.name for path in asset_paths),
        "asset_checksums": named_checksums,
    }
    checkpoint = release_status(
        repo,
        version,
        remote=remote,
        repository=repository,
        expected_release=expected,
    )
    if checkpoint["next_stage"] not in {"github_release", "completed"}:
        raise ReleaseError(f"Tag {tag} 尚未在 Remote 完成严格验证")
    local = _local_tag_facts(repo, tag)
    if checkpoint["next_stage"] == "completed":
        payload = checkpoint["github_release_facts"]
        if not isinstance(payload, dict):
            raise ReleaseError("已验证 Release facts 缺失")
        return _release_details(
            repository=repository,
            remote=remote,
            tag=tag,
            local=local,
            payload=payload,
            expected=expected,
            asset_checksums=named_checksums,
            expected_account=expected_account,
            expected_protocol=expected_protocol,
            already_verified=True,
            provider_tag={
                "object": str(checkpoint["github_tag_object"]),
                "target": str(checkpoint["github_tag_target"]),
            },
        )
    argv = [
        "gh",
        "release",
        "create",
        "--repo",
        repository,
        "--verify-tag",
        "--notes",
        notes,
        "--title",
        title,
    ]
    if draft:
        argv.append("--draft")
    if prerelease:
        argv.append("--prerelease")
    argv.extend(["--", tag, *(str(path) for path in asset_paths)])
    try:
        run(argv, cwd=repo, env=github_env(repository))
    except CommandError as exc:
        raise ReleaseError("GitHub Release 创建失败") from exc
    payload = _read_github_release(repo, repository, tag)
    if payload is None or not _release_matches(
        payload,
        repository=repository,
        tag=tag,
        branch=str(checkpoint["branch"]),
        target=local["target"],
        expected=expected,
    ):
        raise ReleaseError("GitHub Release postflight 不一致")
    return _release_details(
        repository=repository,
        remote=remote,
        tag=tag,
        local=local,
        payload=payload,
        expected=expected,
        asset_checksums=named_checksums,
        expected_account=expected_account,
        expected_protocol=expected_protocol,
        already_verified=False,
        provider_tag={
            "object": str(checkpoint["github_tag_object"]),
            "target": str(checkpoint["github_tag_target"]),
        },
    )


def release_status(
    repo: Path,
    version: str,
    *,
    remote: str,
    repository: str | None = None,
    expected_release: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """只读重建 Tag 与 GitHub Release checkpoint，并给出唯一下一阶段。"""
    from .github import validate_repository_name
    from .remote import validate_remote_name

    remote = validate_remote_name(repo, remote, require_configured=True)
    if repository is not None:
        repository = validate_repository_name(repository)
    if (repository is None) is not (expected_release is None):
        raise ReleaseError("repository 与 expected_release 必须同时提供")
    tag = validate_tag_name(repo, f"v{version}")
    local = _local_tag_facts(repo, tag)
    remote_facts = _remote_tag_facts(repo, remote, tag)
    branch = run(["git", "branch", "--show-current"], cwd=repo).stdout.strip()
    github_release = False
    release_facts: dict[str, Any] | None = None
    release_state = "not_checked"
    github_tag: dict[str, str] | None = None
    if not local["exists"] and remote_facts["exists"]:
        raise ReleaseError("Remote 已存在同名 Tag，但本地缺失，拒绝猜测 checkpoint")
    if not local["exists"]:
        next_stage = "annotated_tag"
    elif not remote_facts["exists"]:
        next_stage = "push_tag"
    else:
        if (
            local["object"] != remote_facts["object"]
            or local["target"] != remote_facts["target"]
        ):
            raise ReleaseError("本地与 Remote annotated Tag 身份不一致")
        next_stage = "github_release"
        if repository is not None and expected_release is not None:
            github_tag = _github_tag_facts(repo, repository, tag)
            if (
                github_tag["object"] != local["object"]
                or github_tag["target"] != local["target"]
            ):
                raise ReleaseError(
                    "GitHub Provider Tag object/target 与本地和 Remote Tag 不一致"
                )
            release_facts = _read_github_release(repo, repository, tag)
            if release_facts is None:
                release_state = "missing"
            elif _release_matches(
                release_facts,
                repository=repository,
                tag=tag,
                branch=branch,
                target=local["target"],
                expected=expected_release,
            ):
                github_release = True
                release_state = "already_verified"
                next_stage = "completed"
            else:
                raise ReleaseError("GitHub Release 已存在但与批准事实冲突")
    return {
        "schema_version": "1",
        "version": version,
        "tag": tag,
        "repository": repository,
        "local_tag": local["exists"],
        "remote_tag": remote_facts["exists"],
        "github_release": github_release,
        "release_status": release_state,
        "github_release_facts": release_facts,
        "github_tag_object": github_tag.get("object") if github_tag else None,
        "github_tag_target": github_tag.get("target") if github_tag else None,
        "local_tag_object": local.get("object"),
        "local_tag_target": local.get("target"),
        "remote_tag_object": remote_facts.get("object"),
        "remote_tag_target": remote_facts.get("target"),
        "branch": branch,
        "next_stage": next_stage,
        "writes_performed": False,
    }
