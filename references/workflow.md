# 确定性工作流

## Facts 与计划

inspect 使用 `git status --porcelain=v2 -z --branch`、HEAD、当前操作标记和 Remote facts。
所有路径按字节安全边界处理；面向用户显示时才做可读转义。

plan 固定 action、repo、params、precondition fingerprint、schema version 和 canonical
SHA-256。Apply 必须同时满足：

1. 用户批准值等于已展示 plan hash；
2. plan hash 自身未变；
3. 当前 fingerprint 等于 precondition；
4. 仓库互斥锁可获得；
5. 本阶段专属前置条件成立。

## Commit

先验证 local/global identity 来源和可信回归。批准路径通过 NUL 分隔 pathspec 输入给
Git；staged 集合必须与批准集合完全相等。Commit 前备份 index，失败只恢复 index，
不删除或重置工作区文件。Commit 后验证新 HEAD 和提交文件集合再保存 record。

## Remote 与 Push

GitHub 仓库创建不隐式 Push。Remote URL 若已存在但不同则停止。Push 前 fetch/prune，
计算 ahead/behind；behind 或 diverged 停止。只使用普通 Push，postflight 用远端 ref
OID 对比本地 HEAD。

## 恢复

恢复要求 operation record、owned 标志、备份 checksum 和当前事实均匹配。未知记录、
漂移备份或公开资源只解释，不自动撤销。先用 `plan-recover` 根据受管 record 生成新的
不可变恢复计划，向用户展示并取得该计划自己的 approval hash，再用 `recover` 应用。
恢复前还要确认当前 index 与原操作完成后的 checksum 一致；恢复时先保存 undo backup，
postflight 校验成功后才记录完成。永远不以删除用户文件作为“恢复”。
