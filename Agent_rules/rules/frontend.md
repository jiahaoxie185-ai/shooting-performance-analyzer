# 前端使用约束

## 技术与目录

- 前端只保留在 `web/`，不重建 `fronted/` 或新增重复前端目录。
- 使用现有 Next.js App Router、React、JavaScript 和 CSS；依赖版本以 `web/package.json` 和 `web/package-lock.json` 为准。
- 页面入口为 `web/app/page.js`，根布局为 `web/app/layout.js`；可复用业务组件放在 `web/components/`。
- 需要状态、事件或浏览器 API 的组件明确使用客户端组件边界。当前首页使用 `"use client"`。

## API 与登录

- 前端通过 HTTP 使用后端接口，不直接访问 SQLite，也不在前端保存数据库访问逻辑。
- 登录提交 JSON `{username, password}` 到 `POST /auth/login`；成功后保存用户视图状态并进入训练工作台。
- 页面初始化调用 `GET /auth/me` 恢复有效会话；401 时进入未登录状态。
- 退出调用 `POST /auth/logout`，成功后清除前端用户状态并返回登录或欢迎视图。
- 登录令牌由后端通过 HttpOnly Cookie 管理，不将其复制到 localStorage，也不尝试用 JavaScript 读取。
- API 请求集中在 `web/lib/api.js`，使用 `/api` 同源代理并携带凭据。`web/next.config.mjs` 的 `BACKEND_URL` 默认指向本地 8000；配置改变后需重启或重新构建前端，不额外开启 CORS。
- 不把密码、Cookie、令牌或敏感响应写入控制台或持久化存储。

## 训练与统计展示

- 实现创建训练、添加投篮、结束训练、训练列表、单场详情、总体与分区统计。
- 区域值与后端 `ShootingZone` 保持一致，可映射为中文标签；不自行添加未约定的区域值。
- API 的 `field_goals` 为 0～1，展示时乘以 100 并加 `%`；统一展示精度，原始值不改写。
- 累计命中率使用后端统计结果，不平均各场百分比。
- 表单处理输入、提交、加载、成功和错误状态；提交期间防止重复操作。
- 训练结束后禁用新增投篮操作，同时由后端进行最终状态校验。
- 列表、详情和统计均提供加载、空数据和失败状态；表单使用对应 label 和合适的按钮类型。

## 当前边界与检查

- 当前注册、登录、刷新恢复和退出已接入后端；Dashboard 显示当前用户信息，训练功能仍为标题占位，不描述为已完成训练功能。
- 现有脚本：在 `web/` 执行 `npm run dev`、`npm run build`、`npm run start`、`npm run lint`。
- 前端没有 package.json 测试脚本；独立请求模块验证使用 `node --test validation/api.test.mjs`（根目录）。lint 和 build 分别验证代码规范与构建，不能替代浏览器流程验证。原 `test/` 仍按用户要求忽略。
- 新增依赖需有具体用途，同步维护依赖清单和锁文件；不要无目的升级技术栈。
