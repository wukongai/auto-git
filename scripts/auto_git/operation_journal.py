"""原子操作日志：先记录开始，再保存成功、部分执行或未知结果。"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .git_facts import inspect_repo
from .state import atomic_write_json


REMOTE_ACTIONS = {"push", "push_tag", "github_repo_create", "github_release"}


def _now() -> str:
    """统一使用UTC保存机器时间，用户展示由宿主转换。"""
    return datetime.now(timezone.utc).isoformat()


def expected_details(plan: dict[str, Any]) -> dict[str, Any]:
    """只保存重新核验所需的脱敏目标，不复制原始参数或命令输出。"""
    params = plan["params"]
    action = plan["action"]
    if action == "configure_identity":
        return {"scope": "local", "name": params["name"], "email_hash": hashlib.sha256(params["email"].encode()).hexdigest()}
    if action == "stage_commit":
        return {"paths": list(params["paths"])}
    if action == "push":
        preflight = params.get("remote_preflight", {})
        target = preflight.get("local_head")
        return {"name": params.get("remote", "origin"), "branch": params["branch"], "local": target, "remote": target, "url_identity": preflight.get("url_identity")}
    if action == "remote_connect":
        from .remote import normalize_remote_url
        return {"name": params.get("name", "origin"), "url_identity": normalize_remote_url(params["url"])}
    if action == "init":
        return {"branch": params.get("branch", "main")}
    if action in {"tag", "push_tag", "github_release"}:
        from .release import _local_tag_facts
        from .runner import run
        tag = params.get("tag") or f"v{params['version']}"
        repo = Path(plan["repo"])
        local = _local_tag_facts(repo, tag)
        head = run(["git", "rev-parse", "HEAD"], cwd=repo, check=False).stdout.strip() or None
        details = {"tag": tag, "object": local.get("object"), "target": local.get("target", head), "existed_before": bool(local.get("exists"))}
        if action == "push_tag":
            from .remote import normalize_remote_url
            remote = params.get("remote", "origin")
            endpoint = run(["git", "remote", "get-url", "--push", "--", remote], cwd=repo).stdout.strip()
            details.update(remote=remote, url_identity=normalize_remote_url(endpoint))
        if action == "github_release":
            assets = params.get("assets", [])
            checksums = params.get("asset_checksums", {})
            branch = run(["git", "branch", "--show-current"], cwd=repo).stdout.strip()
            details.update(
                repository=params["repository"], remote=params["remote"], hostname="github.com",
                title=params["title"], draft=params["draft"], prerelease=params["prerelease"],
                notes_sha256=hashlib.sha256(params["notes"].encode("utf-8")).hexdigest(),
                assets=sorted(Path(value).name for value in assets),
                asset_checksums={Path(value).name: checksum for value, checksum in checksums.items()},
                tag_object=local.get("object"), provider_tag_object=local.get("object"),
                provider_tag_target=local.get("target"), expected_branch=branch,
            )
        return details
    if action == "github_repo_create":
        return {
            "name": params["name"], "visibility": params["visibility"], "hostname": "github.com",
            "url_identity": f"https://github.com/{params['name']}",
            "authenticated_account": params["authenticated_account"], "git_protocol": params["git_protocol"],
        }
    return {}


class OperationJournal:
    """拥有单个计划记录；未完成记录永不作为可自动重放授权。"""

    def __init__(self, plan: dict[str, Any], state_home: Path):
        self.plan = plan
        self.path = state_home / "records" / f"{plan['id']}.json"
        self.record = {
            "schema_version": "1", "plan_id": plan["id"],
            "plan_hash": plan["plan_hash"], "repo": plan["repo"],
            "action": plan["action"], "status": "running", "owned": True,
            "details": expected_details(plan), "started_at": _now(),
            "next_step": "操作中；若会话中断，先只读核验，再决定继续方式",
        }

    def start(self) -> None:
        """在任何业务写入前持久化running。"""
        atomic_write_json(self.path, self.record)

    def success(self, details: dict[str, Any]) -> dict[str, Any]:
        """保留兼容成功字段，并固定实际完成时间。"""
        self.record.update(status="succeeded", details=details, completed_at=_now(),
                           index_backup=details.get("index_backup"),
                           next_step="读取本次核验结果；下一动作另行预览和批准")
        atomic_write_json(self.path, self.record)
        return deepcopy(self.record)

    def failure(self, error: Exception) -> dict[str, Any]:
        """依据实际副作用分类，远程读取不确定时绝不声称未执行。"""
        details = deepcopy(self.record["details"])
        error_details = getattr(error, "details", None)
        if isinstance(error_details, dict):
            details.update(error_details)
        action = self.plan["action"]
        if getattr(error, "commit_created", False):
            status = "verification_failed"
        elif action == "tag":
            # Tag refs不在工作区指纹中，读取中断时不能声称没有副作用。
            status = "unknown"
        elif action in REMOTE_ACTIONS and not getattr(error, "before_remote_write", False):
            status = "unknown"
        else:
            try:
                unchanged = inspect_repo(Path(self.plan["repo"]))["fingerprint"] == self.plan["precondition_fingerprint"]
            except (OSError, RuntimeError, ValueError):
                unchanged = False
            status = "failed" if unchanged else "partial"
        next_step = (
            "先只读核对目标Tag或远端及Commit，区分已应用与结果未知；不要盲目重试"
            if status == "unknown" else
            "保留当前文件与已发生历史；读取实际差异，重新生成最小继续计划"
        )
        # 底层stderr可包含完整diff或任意正文；持久化只保存稳定分类和安全短说明。
        message = "操作未通过安全核验；保留现场，先读取状态和本次安全回执"
        self.record.update(status=status, details=details, completed_at=_now(),
                           error={"type": type(error).__name__, "code": status, "message": message},
                           next_step=next_step, index_backup=details.get("index_backup"))
        atomic_write_json(self.path, self.record)
        return deepcopy(self.record)
