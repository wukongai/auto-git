"""Auto Git 薄 CLI；所有业务逻辑留在独立模块。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .doctor import doctor
from .executor import apply_plan, verify_record
from .git_facts import inspect_repo
from .github import auth_status
from .install import dependency_plan
from .planner import create_plan
from .recovery import create_recovery_plan
from .redaction import redact
from .remote import verify_mirror_refs
from .release import check_readiness, load_release_profile, release_status
from .state import (
    atomic_write_json,
    default_state_home,
    operation_history,
    read_json,
)


_JSON_REQUESTED = False


class _StableArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if _JSON_REQUESTED:
            print(
                json.dumps(
                    {
                        "schema_version": "1",
                        "status": "error",
                        "error": {
                            "type": "ArgumentError",
                            "message": redact(message),
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            raise SystemExit(2)
        super().error(message)


def _parser() -> argparse.ArgumentParser:
    parser = _StableArgumentParser(prog="auto-git", allow_abbrev=False)
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=_StableArgumentParser,
    )
    for name in ("doctor", "inspect"):
        command = subparsers.add_parser(name, allow_abbrev=False)
        command.add_argument("--repo", type=Path, required=True)
        command.add_argument("--json", action="store_true")
    dependency = subparsers.add_parser("dependency-plan", allow_abbrev=False)
    dependency.add_argument("--dependency", choices=("git", "gh"), required=True)
    dependency.add_argument("--system")
    dependency.add_argument("--json", action="store_true")
    auth = subparsers.add_parser("auth-status", allow_abbrev=False)
    auth.add_argument("--provider", choices=("github",), required=True)
    auth.add_argument("--json", action="store_true")
    plan = subparsers.add_parser("plan", allow_abbrev=False)
    plan.add_argument("--repo", type=Path, required=True)
    plan.add_argument("--action", required=True)
    plan.add_argument("--params-json", default="{}")
    plan.add_argument("--output", type=Path)
    plan.add_argument("--json", action="store_true")
    apply = subparsers.add_parser("apply", allow_abbrev=False)
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--approval", required=True)
    apply.add_argument("--state-home", type=Path)
    apply.add_argument("--json", action="store_true")
    verify = subparsers.add_parser("verify", allow_abbrev=False)
    verify.add_argument("--record", type=Path, required=True)
    verify.add_argument("--json", action="store_true")
    plan_recover = subparsers.add_parser("plan-recover", allow_abbrev=False)
    plan_recover.add_argument("--repo", type=Path, required=True)
    plan_recover.add_argument("--record", type=Path, required=True)
    plan_recover.add_argument("--state-home", type=Path, required=True)
    plan_recover.add_argument("--output", type=Path)
    plan_recover.add_argument("--json", action="store_true")
    recover = subparsers.add_parser("recover", allow_abbrev=False)
    recover.add_argument("--plan", type=Path, required=True)
    recover.add_argument("--approval", required=True)
    recover.add_argument("--state-home", type=Path, required=True)
    recover.add_argument("--json", action="store_true")
    resume = subparsers.add_parser("resume", allow_abbrev=False)
    resume.add_argument("--repo", type=Path, required=True)
    resume.add_argument("--version", required=True)
    resume.add_argument("--remote", default="origin")
    resume.add_argument("--repository", required=True)
    resume.add_argument("--expected-json", required=True)
    resume.add_argument("--json", action="store_true")
    verify_mirrors = subparsers.add_parser("verify-mirrors", allow_abbrev=False)
    verify_mirrors.add_argument("--repo", type=Path, required=True)
    verify_mirrors.add_argument("--remote", action="append", required=True)
    verify_mirrors.add_argument("--branch", required=True)
    verify_mirrors.add_argument("--tag")
    verify_mirrors.add_argument("--json", action="store_true")
    release_check = subparsers.add_parser("release-check", allow_abbrev=False)
    release_check.add_argument("--repo", type=Path, required=True)
    release_check.add_argument("--version", required=True)
    profile_source = release_check.add_mutually_exclusive_group()
    profile_source.add_argument("--profile", type=Path)
    profile_source.add_argument("--profile-json")
    release_check.add_argument("--regression-json")
    release_check.add_argument("--build-json")
    release_check.add_argument("--json", action="store_true")
    history = subparsers.add_parser("history", allow_abbrev=False)
    history.add_argument("--repo", type=Path, required=True)
    history.add_argument("--state-home", type=Path)
    history.add_argument("--json", action="store_true")
    return parser


def _execute(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "doctor":
        payload: dict[str, Any] = doctor(args.repo)
    elif args.command == "inspect":
        payload = inspect_repo(args.repo)
    elif args.command == "dependency-plan":
        payload = dependency_plan(args.dependency, system=args.system)
    elif args.command == "auth-status":
        payload = auth_status()
    elif args.command == "plan":
        if args.action == "recover_index":
            raise ValueError("recover_index 必须使用 plan-recover 创建受管恢复计划")
        params = json.loads(args.params_json)
        payload = create_plan(args.action, args.repo, params)
        if args.output:
            atomic_write_json(args.output, payload)
    elif args.command == "apply":
        payload = apply_plan(
            read_json(args.plan),
            approval=args.approval,
            state_home=args.state_home,
        )
    elif args.command == "verify":
        payload = verify_record(read_json(args.record))
    elif args.command == "plan-recover":
        payload = create_recovery_plan(
            args.record,
            repo=args.repo,
            state_home=args.state_home,
        )
        if args.output:
            atomic_write_json(args.output, payload)
    elif args.command == "recover":
        plan = read_json(args.plan)
        if not isinstance(plan, dict) or plan.get("action") != "recover_index":
            raise ValueError("recover 只接受 plan-recover 生成的恢复计划")
        payload = apply_plan(
            plan,
            approval=args.approval,
            state_home=args.state_home,
        )
    elif args.command == "resume":
        expected_release = json.loads(args.expected_json)
        if not isinstance(expected_release, dict):
            raise ValueError("expected-json 必须是 Release 期望对象")
        payload = release_status(
            args.repo,
            args.version,
            remote=args.remote,
            repository=args.repository,
            expected_release=expected_release,
        )
    elif args.command == "verify-mirrors":
        payload = verify_mirror_refs(
            args.repo,
            remotes=args.remote,
            branch=args.branch,
            tag=args.tag,
        )
    elif args.command == "release-check":
        if args.profile_json:
            profile = json.loads(args.profile_json)
        else:
            profile_path = args.profile or args.repo / ".auto-git.toml"
            profile = load_release_profile(profile_path) if profile_path.is_file() else None
        regression = (
            json.loads(args.regression_json) if args.regression_json else None
        )
        build = json.loads(args.build_json) if args.build_json else None
        if (
            (profile is not None and not isinstance(profile, dict))
            or (regression is not None and not isinstance(regression, list))
            or (build is not None and not isinstance(build, list))
        ):
            raise ValueError("regression/build 必须是 JSON 命令数组")
        payload = check_readiness(
            args.repo,
            args.version,
            profile=profile,
            regression=regression,
            build=build,
        )
    elif args.command == "history":
        payload = operation_history(
            args.repo,
            args.state_home or default_state_home(),
        )
    else:
        raise ValueError(f"未知命令：{args.command}")
    return payload


def _print_human(payload: dict[str, Any]) -> None:
    labels = {
        "path": "路径",
        "is_repo": "仓库",
        "status": "状态",
        "ready": "可发布",
        "authenticated": "已认证",
        "verified": "已验证",
        "writes_performed": "已执行写入",
        "next_stage": "下一阶段",
        "plan_hash": "审批哈希",
        "id": "计划 ID",
    }
    preferred = [key for key in labels if key in payload]
    if not preferred:
        preferred = [
            key
            for key in payload
            if key not in {"schema_version", "fingerprint"}
        ]
    for key in preferred:
        value = payload[key]
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            rendered = "是" if value else "否"
        else:
            rendered = str(value)
        print(f"{labels.get(key, key)}：{rendered}")


def main(argv: list[str] | None = None) -> int:
    global _JSON_REQUESTED
    effective_argv = list(argv) if argv is not None else sys.argv[1:]
    _JSON_REQUESTED = "--json" in effective_argv
    args = _parser().parse_args(effective_argv)
    try:
        payload = _execute(args)
    except (RuntimeError, ValueError, OSError, KeyError, TypeError) as exc:
        message = redact(str(exc)) or "未知错误"
        if getattr(args, "json", False):
            print(
                json.dumps(
                    {
                        "schema_version": "1",
                        "status": "error",
                        "error": {
                            "type": type(exc).__name__,
                            "message": message,
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"错误[{type(exc).__name__}]：{message}", file=sys.stderr)
        return 2
    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_human(payload)
    return 0
