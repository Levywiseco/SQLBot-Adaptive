# 团队提交与本次合并说明

目标仓库：https://github.com/Levywiseco/SQLBot-Adaptive

## 本次合并

来源：icecoding0305/SQLBot-Adaptive 的 sqlbot-ice 分支。
来源提交：6a93a121236a9d2b2f38bdedd73c287177b7cd5b，共 5 次提交。

包含界面调整、用户数据源访问配置、操作审计、管理员修改用户密码及加密传输调整。
保留原作者和提交历史。集成时修复已有的 AI 错误日志展示问题，并将开发 API 默认端口恢复为项目启动脚本使用的 8000。
需要 8020 的开发者可以在 frontend/.env.development.local 中设置 VITE_API_BASE_URL=http://localhost:8020/api/v1。

## 协作者首次设置

1. 使用自己的 GitHub 账号接受仓库协作者邀请。
2. 在自己的本地项目中添加目标远程仓库（若 team 已存在，先用 git remote -v 检查地址）：

```bash
git remote add team https://github.com/Levywiseco/SQLBot-Adaptive.git
git fetch team
```

3. 本次 sqlbot-ice 修改已经合并，后续从最新主分支创建工作分支：

```bash
git switch -c feat/my-next-change team/main
# 修改并提交代码后
git push -u team HEAD
```

这样分支直接上传到团队仓库，不再需要先上传个人 fork。
推荐对 main 发起 Pull Request。仓库未启用主分支保护时，有写权限的协作者也可以直接推送 main：

```bash
git switch main
git pull --ff-only team main
# 修改、验证、提交后
git push team main
```

如果同步提示分支已分叉，先合并或变基并处理冲突，不要强制推送。
HTTPS 登录使用协作者自己的 GitHub 令牌/凭据管理器，或者使用自己的 SSH 密钥；不要共享仓库所有者的账号或令牌。
如果接受邀请后仍提示 403，请检查当前认证账号以及令牌对此仓库的 Contents 写权限。

## 更新已有部署

- 备份项目元数据库，使用正常升级流程执行 backend 下的 `alembic upgrade head`。本次新增迁移 c91f40a73b02，创建 sys_user_datasource 表。
- 配置并持久保存 SECRET_KEY；新加密的模型配置依赖该值解密，重启或更新时不可随意更换。
- 当前登录 RSA 私钥在进程启动时生成。API 暂按单 worker 部署，重启后刷新浏览器；多实例或多 worker 上线前需要改为共享持久密钥或相应密钥轮换机制。
- 非 localhost 访问需 HTTPS，新的浏览器加密依赖 Web Crypto 安全上下文。
- 代码合并不等于数据库升级或运行中服务已更新。上线前验证登录、普通用户的数据源隔离、密码修改、审计导出和模型调用。
