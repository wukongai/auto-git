# Release 分阶段契约

readiness 必须同时验证版本事实、CHANGELOG、干净工作区、full regression、build、Tag
冲突和 assets。未就绪只输出阻断项，不进入写入阶段。

项目必须先提供 `.auto-git.toml` 的显式 `[release]` profile，至少固定版本文件、
Changelog 文件/章节、允许分支、Tag 模板、Remote、必需 assets、draft/prerelease、
回归和构建 argv。缺少 profile 或必要字段时只报告阻断项，不从聊天猜默认值。

```toml
[release]
version_file = "VERSION"
changelog_file = "CHANGELOG.md"
changelog_section = "## [{version}]"
allowed_branches = ["main"]
tag_template = "v{version}"
remote = "origin"
required_assets = ["SKILL.md", "skill.contract.yaml"]
draft = false
prerelease = false
regression = [["python3", "-m", "pytest", "-q"]]
build = [["python3", "-m", "compileall", "-q", "scripts"]]
```

检查还必须 fetch 并验证 upstream 不落后/不分叉、同名本地/远端 Tag 均不存在，以及
每个必需 asset 是受限项目相对路径。Release plan 会固定 asset SHA-256。

阶段和审批不可合并：

1. Release Commit；
2. annotated Tag；
3. branch Push；
4. 单个 Tag Push；
5. GitHub Release。

每个阶段完成后保存本地与远端 OID/checkpoint。GitHub Release 使用已存在 Tag 并要求
provider 验证 Tag，不隐式创建 Tag。resume 重新读取事实：相同资源视为幂等完成；缺失
资源从下一阶段继续；同名不同 OID/内容则停止。不得删除、覆盖或改写公开历史。

GitHub 主源与 Gitee 镜像的每次 Push 仍须分别审批。两个远程完成后，运行只读
postflight：

```bash
python3 scripts/auto_git.py verify-mirrors \
  --repo <项目路径> \
  --remote origin --remote gitee \
  --branch main \
  --tag <版本号> \
  --json
```

该检查要求两个远程的 branch OID 都等于本地 HEAD；传入版本号时，还要求本地为
annotated Tag，且两个远程的 annotated Tag target 都等于本地 Tag target。缺少任一
ref、类型错误或 OID 不一致都必须停止，不得报告“双仓发布完成”。
