# 无 Docker 开发与验证手册

## 1. 开发拓扑

Docker 不是 SQLBot 源码开发的必需条件。本项目当前采用：

- Windows：Git、Python 3.11、uv、Node.js 22、FastAPI、Vue/Vite。
- WSL2 Ubuntu：PostgreSQL 17 和 pgvector 0.8.6。
- Windows 后端通过 WSL 当前 IP 访问 PostgreSQL；启动脚本会自动探测地址。
- Embedding 可先关闭；安装完整模型快照后再启用。

本机已经验证的版本见[实施状态](IMPLEMENTATION_STATUS.md)。原生 Linux、远程 PostgreSQL 或 Docker PostgreSQL 也能使用，只要 `.env` 指向可访问且安装了 pgvector 的 PostgreSQL。

## 2. 首次准备

从固定上游版本建立独立分支：

```powershell
Set-Location D:\python
git clone --branch v1.10.1 https://github.com/dataease/SQLBot.git SQLBot-adaptive
Set-Location D:\python\SQLBot-adaptive
git remote rename origin upstream
git switch -c codex/sqlbot-adaptive
```

创建本地配置。真实密码和密钥只写入被 Git 忽略的 `.env`：

```powershell
Copy-Item .env.example .env
notepad .env
```

元数据库必须预先安装 pgvector，并为应用创建独立数据库和账户。以管理员身份在 PostgreSQL 中执行等价操作：

```sql
CREATE ROLE sqlbot_dev LOGIN PASSWORD '<local-password>';
CREATE DATABASE sqlbot_dev OWNER sqlbot_dev;
\c sqlbot_dev
CREATE EXTENSION IF NOT EXISTS vector;
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

安装锁定依赖并迁移：

```powershell
Set-Location D:\python\SQLBot-adaptive\backend
uv sync --extra cpu
uv run alembic upgrade head

Set-Location D:\python\SQLBot-adaptive\frontend
npm ci
```

后端严格要求 Python 3.11。系统默认 Python 可以是其他版本，只要 `backend\.venv` 是 uv 创建的 3.11 环境。

## 3. 启动和停止

终端 A：

```powershell
Set-Location D:\python\SQLBot-adaptive
.\scripts\start-dev-backend.ps1
```

终端 B：

```powershell
Set-Location D:\python\SQLBot-adaptive
.\scripts\start-dev-frontend.ps1
```

打开 `http://127.0.0.1:5173`。后端 API 为 `http://127.0.0.1:8000/api/v1`。停止两个前台进程后，可停止 WSL 开发数据库：

```powershell
.\scripts\stop-dev-database.ps1
```

`start-dev-database.ps1` 只管理本项目带路径标记的 WSL keepalive 进程，并检查 5432 端口；不会递归删除或移动任何目录。

## 4. 加载可复核的合成演示

先创建虚构销售表、SQLBot 数据源元数据和“净销售额 v1”指标，再生成记忆、问数记录和待审核候选：

```powershell
Set-Location D:\python\SQLBot-adaptive\backend
uv run --no-sync python ..\scripts\seed-adaptive-demo.py
uv run --no-sync python ..\scripts\seed-adaptive-learning-demo.py
```

两个脚本都可重复执行。演示数据不含真实业务信息。登录后可以依次打开“指标库”“我的记忆”“学习中心”，再进入 `Adaptive learning demo (synthetic)` 对话查看结果和反馈按钮。

## 5. 自动验证

后端定向测试与静态检查：

```powershell
Set-Location D:\python\SQLBot-adaptive\backend
uv run --no-sync pytest ..\tests\test_adaptive_memory.py ..\tests\test_evaluation_runner.py -q
uv run --no-sync ruff check apps/metrics apps/memory apps/feedback apps/learning `
  ..\tests\test_adaptive_memory.py ..\tests\test_evaluation_runner.py `
  ..\scripts\seed-adaptive-demo.py ..\scripts\seed-adaptive-learning-demo.py `
  ..\scripts\smoke-adaptive.py --ignore UP045
uv run --no-sync python -m compileall -q apps/metrics apps/memory apps/feedback apps/learning
```

后端运行后执行真实 API 生命周期烟雾测试：

```powershell
uv run --no-sync python ..\scripts\smoke-adaptive.py
```

前端类型、浏览器和生产构建验证：

```powershell
Set-Location D:\python\SQLBot-adaptive\frontend
npm exec vue-tsc -- -b

Set-Location D:\python\SQLBot-adaptive
node scripts\ui-smoke-adaptive.cjs

Set-Location D:\python\SQLBot-adaptive\frontend
npm run build
```

默认构建面向现代浏览器。只有确实需要额外旧浏览器 polyfill 时运行 `npm run build:legacy`；这个模式耗时和内存更高。

评测合同示例：

```powershell
Set-Location D:\python\SQLBot-adaptive\backend
uv run --no-sync python ..\evaluations\run.py `
  --cases ..\evaluations\cases.demo.yaml `
  --actual ..\evaluations\results.demo.reference.json `
  --report ..\evaluations\reports\demo.md
```

## 6. 接入真实业务环境

代码以外还需要以下输入才能完成业务验收：

1. 一个只读业务数据源和 5–10 张首期表的字段/JOIN 说明。
2. 由口径负责人确认的首批指标、时间归属、退款/取消、多币种等规则。
3. 一个系统默认 LLM；固定模型、温度和版本后再采集基线。
4. 50–100 条脱敏问题，明确开发集与留出集，附预期结果或可执行参考 SQL。
5. 试点用户与权限矩阵。

当前演示环境没有系统默认 LLM。打开合成历史对话时，原有“推荐问题”接口可能在后端记录“未设置默认模型”，但不会影响已经保存的结果、指标/记忆来源或反馈闭环。
