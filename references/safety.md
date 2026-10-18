# 安全、审批与失败边界

## 永久禁止

- 宽泛暂存、force push、破坏性 reset/clean；
- 自动 stash、自动搬运脏改动、自动解决冲突；
- shell 字符串执行或把路径/消息拼进命令；
- 接收或持久化 Token、密码、私钥、Cookie；
- 绕过回归、hook、受保护分支或远端 non-fast-forward；
- 用一个批准覆盖 Commit、Remote、Push、Tag 和 Release。

## 失败行为

命令缺失、超时和非零退出都是失败。部分成功必须按 checkpoint 报告：哪些本地/远端
事实已经存在，哪些尚未执行，继续是否幂等。计划漂移只允许重新 inspect/plan，禁止
临时修改原计划继续。

测试真实写入时只能使用临时仓库、本地 bare remote 和 fake provider；不得把开发自测
指向用户真实项目或真实 GitHub 账号。
