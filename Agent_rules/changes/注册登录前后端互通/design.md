# 注册登录前后端互通：设计

对应需求：[注册登录前后端互通](../2026-10-01-注册登录前后端互通.md)。本文件为 Planner 阶段产出；实际检查结果由 Generator 和 Evaluator 记录，不把设计目标视为已通过。

## 调查结果与证据

| 能力 | 当前情况 | 证据路径与符号 |
| --- | --- | --- |
| 用户注册 | 校验用户名是否重复，Argon2 哈希后提交真实用户，HTTP 201；重复用户 409 | `api/router/users.py:sign_up`、`application/user_services.py:UserService.sign_up`、`infrastructure/security.py` |
| 密码登录 | 查用户名并校验密码，保存令牌 SHA3-256 摘要，返回实际 User 与原始令牌 | `application/user_services.py:UserService.login` |
| Cookie | 登录路由设置 HttpOnly、SameSite=Lax、7 天 Cookie；Secure 当前固定 False | `api/router/auth.py:login` |
| 恢复与退出 | 通过 Cookie 查有效会话，退出删除会话及 Cookie | `api/router/auth.py:me/logout`、`application/user_services.py:current_user/logout` |
| 数据持久化 | 工作单元显式提交；用户、会话两张表结构已足够 | `infrastructure/unit_of_work.py`、`infrastructure/models.py:UserModel/AuthSession` |
| 表单 | 有输入和按钮，没有提交处理及反馈状态 | `web/components/LoginForm.js`、`web/components/RegisterForm.js` |
| 首页 | 只有 screen，没有当前用户或恢复流程，Dashboard 无用户信息 | `web/app/page.js:Home`、`web/components/Dashboard.js` |
| 访问配置 | Next.js 配置为空，没有 API 代理 | `web/next.config.mjs` |

用户要求忽略现有 `test/`，不读取或将其作为契约。未发现可复用的前端请求模块。后端框架依赖版本及生产域名未在需求中确定。

## 访问方案

选择 Next.js 同源代理：浏览器只请求 `/api/users`、`/api/auth/login`、`/api/auth/me`、`/api/auth/logout`。`web/next.config.mjs` 的 rewrite 将 `/api/:path*` 转发到 `${BACKEND_URL}/:path*`；默认后端为 `http://127.0.0.1:8000`，去除末尾斜线。代理配置属于服务端，不向浏览器暴露后端地址。

同源方案无需新增 CORS，浏览器 Cookie 归属于前端实际访问主机。HTTP API 模块集中设置 `credentials: "include"`，避免依赖各调用点配置。必须实测代理是否保留 Set-Cookie 及后续 Cookie；不能仅依靠后端独立测试声称端到端通过。

`BACKEND_URL` 在 Next.js 配置载入或构建时确定，改变配置应重启服务或重新构建。生产可设置为内部后端地址，用户浏览器仍通过前端 HTTPS 同源访问。

## 模块职责与状态

- `web/lib/api.js`：封装注册、登录、当前用户、退出。非 2xx 抛出带 status 的错误；识别后端字符串 detail、Pydantic detail 数组及网络失败，为表单提供可读消息。恢复查询禁用缓存。不记录密码、Cookie 或完整敏感响应。
- `RegisterForm`：受控 username/name/password，真正 form submit，原生 required 与长度校验，提交期间禁用操作。成功回调交给 Home，进入登录页并提示注册成功，不自动登录。
- `LoginForm`：受控 username/password，加载和错误状态，成功将响应 User 交给 Home。可接收注册成功提示及预填用户名。失败保持登录视图。
- `Home`：维护 currentUser、screen、恢复状态及反馈。初始化调用 `/auth/me`，有效用户进入 Dashboard，401 清除用户回欢迎页；网络/服务失败显示恢复错误并提供重试，不假称为有效登录。恢复过程中显示加载；Effect 清理或取消避免卸载后更新与陈旧结果覆盖用户操作。
- `Dashboard`：接收真实 user，展示姓名、用户名和可核对的用户 ID；提供退出按钮、加载与错误反馈，保留现有训练占位内容。退出成功才清除 currentUser 并返回欢迎页，失败允许重试。
- `api/router/auth.py`：复用原业务调用，仅必要地补齐 Cookie 环境配置及显式 Path。Secure 通过 `COOKIE_SECURE` 开关控制，本地默认 False，部署 HTTPS 时设置 True；SameSite=Lax、HttpOnly、Path=/、7 天保持一致。删除 Cookie 使用同样作用域与安全属性。

不将用户、密码或令牌存入 localStorage。登录用户状态仅保存在 React 内存中，刷新依靠 HttpOnly Cookie 恢复。

## 接口契约

| 浏览器 URL | 后端 | 输入 | 成功 | 失败 |
| --- | --- | --- | --- | --- |
| `POST /api/users` | `POST /users` | `{username, name, password}` | 201，UserResponse | 409 重复用户名；422 字段校验 |
| `POST /api/auth/login` | `POST /auth/login` | `{username, password}` | 200，UserResponse + session_token Cookie | 401 密码/账号错误；422 字段校验 |
| `GET /api/auth/me` | `GET /auth/me` | Cookie | 200，UserResponse | 401 无 Cookie、失效或不存在用户 |
| `POST /api/auth/logout` | `POST /auth/logout` | Cookie | 200，`{"message":"已退出登录"}` + 删除 Cookie | 网络/服务异常由前端反馈 |

UserResponse：`id, username, name, created_at, height, position`，不含密码/哈希。username 1～50，name 1～100，password 至少 8 位；保持现有后端契约，不任意修改密码或自动去除密码空格。

## 数据与迁移

沿用 `users` 的真实用户 UUID、唯一用户名和 Argon2 password_hash；沿用 `auth_session` 的摘要主键、用户外键及秒级过期时间。现有 schema 足以实现，无数据库迁移，不删除或重建数据库。正常启动前如表不存在可执行现有 `python -m infrastructure.init_db`，但验证使用独立临时数据库，避免把测试账号写入真实数据。

## 验证设计

1. 新增独立认证集成验证，不使用已有 `test/`：覆盖注册 201、持久化、新数据库 Session 查询、Argon2 验证、重复注册 409、字段 422、错误登录 401 且无新增会话、双账号 ID、Cookie 属性、摘要存储、恢复、无效与过期会话、退出和敏感字段排除。使用独立 SQLite 文件/会话工厂与 FastAPI 依赖 override，连接启用外键，不触碰根数据库。
2. 对请求模块的错误解析、credentials 和 no-store 做必要回归检查，可使用 Node 内置测试避免新增框架。
3. 在 `web/` 执行 lint 与 build；未配置 TypeScript，不宣称 typecheck 已通过。
4. 浏览器运行真实 Next.js 代理与隔离数据库后端：注册 → 登录 → 核对正确用户 → 刷新恢复 → 退出 → 恢复失效；切换两账号并验证错误表单和加载状态。记录 Cookie 与请求成功的证据，不输出原始令牌。
5. 审查差异，确认不扩展训练功能、不修改当前测试、不迁移真实数据库，并同步需求、架构及约束文档。

生产域名和 HTTPS 由部署方提供；本次实现可配置 Secure，不能声称生产部署已验证。任何受环境限制无法执行的浏览器或构建检查必须明确记录。
