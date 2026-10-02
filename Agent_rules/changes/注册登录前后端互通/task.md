# 注册登录前后端互通：任务

需求：[注册登录前后端互通](../2026-10-01-注册登录前后端互通.md)。设计：[design.md](./design.md)。Planner、Generator、Evaluator 阶段已完成；下表记录最终任务状态，人工审查与合并由用户决定。

| 顺序 | 状态 | 目标 / 预计路径 | 完成标准 | 验证方法 |
| --- | --- | --- | --- | --- |
| 1 | 已完成 | 同源访问：`web/next.config.mjs`、`web/lib/api.js`、环境配置示例或说明 | /api rewrite，BACKEND_URL 默认本地 8000；统一 JSON、凭据和错误处理，恢复查询 no-store | 请求模块独立检查；代理实测 POST/GET/Cookie |
| 2 | 已完成 | Cookie 配置：`api/router/auth.py` | HttpOnly、Path=/、7 天、Lax；Secure 可环境配置，删除属性一致 | 隔离数据库 API 验证登录/退出 Set-Cookie，分别验证 Secure 配置 |
| 3 | 已完成 | 注册表单：`web/components/RegisterForm.js` | 受控输入；注册成功回调；失败提示；防重复提交；注册不自动登录 | 注册成功、重复用户名、无效字段浏览器验证 |
| 4 | 已完成 | 登录表单：`web/components/LoginForm.js` | 调用实际接口，成功向父组件回传真实 User，失败不跳转；显示加载和错误 | 正确/错误密码、两个账号浏览器验证 |
| 5 | 已完成 | 状态与工作台：`web/app/page.js`、`web/components/Dashboard.js` | 初始化恢复、401 清空、加载/重试、真实用户展示、退出处理；保留训练占位 | 刷新恢复、无效 Cookie、退出后刷新、账号切换 |
| 6 | 已完成 | 新增独立验证文件，原 `test/` 不动 | 隔离 SQLite 和依赖 override，覆盖需求关键流程，不写真实用户数据库 | 运行新测试/检查，保存实际结果 |
| 7 | 已完成 | 规范与构建：`web/package.json` 现有命令 | lint、build 完成；环境限制或失败如实记录 | `npm run lint`、`npm run build`；TypeScript 未配置 |
| 8 | 已完成 | Evaluator 独立验收、diff 审查 | 对照验收项记录通过/失败/未验证，发现问题回传 Generator | 浏览器端到端、独立 API 验证、git diff 审查 |
| 9 | 已完成 | 同步记录：需求文件、`Agent_rules/doc/项目架构.md`、`Agent_rules/rules/`、本任务文件 | 文档反映最终实现、访问与部署配置、真实验证结果 | 文档与代码核对，向用户交付可审查结果，不自动合并 |

## 依赖

1、2 为前后端接入基础，可按明确文件边界实施；3、4 依赖 1，5 依赖 3、4；6 随实现添加并独立验证；7、8 依赖实现就绪；9 在验收结果明确后完成。

## 保护范围

- 不修改现有 `test/`，不重新创建 `fronted/`。
- 不新增训练接口或统计业务，不升级现有依赖，不修改数据库结构。
- 保留用户已有修改，真实数据库和已有用户数据不用于验证写入。
- 本轮交接不合并、不部署。无法执行的检查必须标记未验证，不勾选为通过。

## 实际验证记录

Planner：已读取需求、workflow 与约束，完成调查和设计。

Generator：已完成 API 模块、rewrite、表单、用户状态与 Cookie 配置；没有新增依赖或迁移。

Evaluator：后端独立认证检查 9 项、前端 API 检查 3 项、lint、生产构建、差异格式检查通过。浏览器认证主流程已实测，详细结果与未测边界见 [evaluation.md](./evaluation.md)。

已同步需求、架构、前后端约束及 web/README.md。Next.js dev 自动生成 web/AGENTS.md 与 web/CLAUDE.md，保留并披露。没有使用当前 test/，真实数据库校验值保持不变，临时服务已停止。未合并、未部署。
