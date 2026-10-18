# Auto Git 六领域文档迁移与门禁验证

## 范围与授权

2026-10-19用户要求先备份，按最新版AEF Docs Init迁移到六领域，保留正文和审核状态，并检查相关链接及门禁。本轮为结构迁移，不改变产品承诺、市场判断、宪法原则或历史审批。

## 备份与恢复

- 项目外完整归档：`/Users/aim5/Documents/CodingProject/auto-git-backups/docs-six-domains-20261019/project-before.tar.gz`，包含未跟踪中间导出文件，排除Git内部数据与缓存。
- 工具事务备份：同目录`transaction/`；包含original、expected、record.json。工具先备份并逐文件回读哈希，再执行迁移。
- 逐文件决策和预览：同目录`decisions.json`、`migration-map.md`、`preview.json`、`apply.json`。78份文档/附件有明确处置；2份旧总导航由合同替换，原文完整留备份，其余正文和模板保留。
- 迁移瞬间的`--verify`已通过，核验145个结果文件；随后补充引用修正、测试和本文。原事务仍保留原始哈希，不修改历史收据。
- 恢复必须先预览；当前已存在后续引用修正，不能直接覆盖。先额外备份当前修改，再审阅恢复差异。不要删除外部备份。

## 当前落点

| 内容 | 路径 |
|---|---|
| 产品定义0.2 | [product-definition](../../../product/product-definition.md) |
| 待解决问题 | [product-questions](../../../product/product-questions.md) |
| 架构 | [auto-git](../../architecture/auto-git.md) |
| 当前产品开发任务 | [任务卡](../../../project/tasks/auto-git-v0.1.0.md) |
| 用户手册 | [中文用户手册](../../../knowledge/users/guides/auto-git-user-manual.zh-CN.md) |
| 本次日志 | [2026-10-19](../../../project/logs/2026-10-19-daily.md) |

六领域及51个静态目录导航已生成；`.aef/docs-layout.json`为机器合同，AGENTS和CLAUDE均接入路由规则。旧模板与旧导航资料保留于相应领域或knowledge/references/legacy-layout，不再作为活跃导航。

## 引用与内容保真

- 迁移工具修复Markdown相对链接、配置路径字段和Agent文档路径；人工补充Wiki链接、绝对路径、测试路径与少量中文标点相邻路径。
- 产品定义仍为version 0.2、status approved；Q-005仍已解决。宪法正文不变，只调整related链接。
- 已审核PDF字节完全不变，SHA-256：`91aa4bca3f646890464191e9395ef4c6babaa56c50cad788862a4eda8c776aa4`。历史PDF/HTML内嵌本机路径不重写，保留审核证据；当前源文链接和重导出结果使用新路径。
- 主文专用导出脚本改为允许docs树内图片，仍拒绝目录外图片与网络图片；迁移后试导出成功、3张PNG正确加载。
- AEF Docs Init检查通过；可解析本地Markdown链接通过，活跃文档Wiki路径检查无缺失。外部网址、动态代码及历史二进制内嵌链接不冒称全覆盖。

## 提交门禁

新增scripts/credential-lint.sh与scripts/pre-commit.sh，本机.git/hooks/pre-commit指向后者。没有修改全局hooksPath。门禁扫描暂存区并执行git diff --cached --check；疑似凭证只报告文件名。

在AEF脚本基础上修正stdin被首个模式消耗导致后续模式漏扫的问题，并取消研究目录免扫。新增临时Git仓库测试：干净提交放行、合成GitHub/OpenAI/私钥标记提交分别阻断，输出不泄露匹配正文。4项通过。

最终全量回归117 passed、1 skipped（含4项新增门禁测试），ruff通过；跳过项为可选布丁projection，不是迁移失败。旧工程adapter再次生成前仍需预览，不能直接以旧模板覆盖六领域规则。
