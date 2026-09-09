# 上线、回滚、上游同步与许可边界

## 试点顺序

1. 先在独立环境执行迁移和合成数据验证，确认原有登录、数据源和问数页面可用。
2. 连接只读业务数据源，固定 LLM 和数据快照，采集未启用扩展的基线。
3. 只维护并发布少量核心指标，先观察命中来源，再启用指标影响答案。
4. 为少量用户启用个人记忆和反馈；共享候选保持人工审批。
5. 使用同一留出集比较正确率、口径一致率、权限、延迟和成本，再扩大范围。

四个 `ADAPTIVE_*` 环境变量可以分别暂停指标召回、记忆召回、反馈写入和共享经验激活。关闭召回不会删除知识，便于立即止损和复盘。管理员仍能撤销已激活经验。

## 数据库变更与回滚

上线前备份 SQLBot 元数据库和上传目录，并记录应用提交、`uv.lock`、`package-lock.json`、模型文件版本及环境配置版本。迁移命令：

```powershell
Set-Location backend
uv run alembic upgrade head
uv run alembic current
```

若新召回行为异常，先关闭对应 answer-time 开关并重启后端；若单条知识异常，在 UI 中暂停、归档或撤销。代码回滚应优先保留新增表，使旧代码忽略它们。`alembic downgrade` 会删除数据，只能在已备份并明确需要销毁新增数据的隔离环境使用。

生产发布前至少演练一次“备份 → 新库恢复 → 应用启动 → 登录 → 核心问数 → 撤销知识”的完整路径，并记录耗时与责任人。

## 上游同步

本分支保留 `upstream=https://github.com/dataease/SQLBot.git`。建议每次只同步一个经过评估的上游标签：

```powershell
git fetch upstream --tags
git switch codex/sqlbot-adaptive
git switch -c codex/rebase-vNEXT
git rebase <approved-upstream-tag>
```

冲突重点通常位于 `backend/apps/api.py`、`backend/apps/chat/task/llm.py`、`backend/apps/chat/models/chat_model.py`、路由、菜单和 i18n。同步后必须重新执行迁移检查、后端测试、API/UI 烟雾测试和生产构建，不能只以 Git 无冲突作为验收。

## 许可与 X-Pack 边界

仓库 `LICENSE` 将 SQLBot 描述为带附加条件的 GPLv3，明确要求在使用前端时不得删除或修改 SQLBot 控制台或应用中的 Logo 与版权信息。当前后端依赖还包含 `sqlbot-xpack`，现有启动和授权逻辑保持原样，本二创不通过修改许可判断来实现功能。

在建立自己的远程仓库、对外分发、提供商业服务或变更品牌前，应根据实际交付方式确认源代码提供义务、Logo/版权限制、第三方依赖许可和 X-Pack 授权范围。内部原型也应保留上游版权、基线标签和修改记录。

## 生产差距

当前代码适合本地演示和进入真实业务联调，还没有完成生产验收。上线前必须补齐：默认 LLM 与密钥管理、真实留出集、业务指标签字、只读数据库账户与查询超时、独立学习 worker、监控告警、备份恢复演练、性能分包和试点结果报告。
