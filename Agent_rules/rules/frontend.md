# 前端使用约束

## 技术与目录

- 前端只保留在 `web/`，不重建 `fronted/` 或新增重复前端目录。
- 使用现有 Next.js App Router、React、JavaScript 和 CSS；依赖版本以 `web/package.json` 和 `web/package-lock.json` 为准。
- 页面入口为 `web/app/page.js`，根布局为 `web/app/layout.js`；可复用业务组件放在 `web/components/`。
- 工作台组件和共享样式放在 `web/components/dashboard/`。详情子页面位于其下的 `singleshootingform/`，页面组件放在 components/，状态与操作逻辑放在 hooks/，请求入口放在 api/。页面组件已连接，状态与请求逻辑由对应 hooks 管理。
- `useShotGroups(sessionId)` 负责本场训练的组列表、创建和更新；创建不选择点位，新增组的 zone 为 null，不自动创建所属训练。后续 SingleShootingForm 负责列表与详情的组织。
- 进行中表单选择点位并填写数量，调用 useFinishShotGroup 的 finishGroup({ zone, attempts, made }) 一次提交；失败保留输入。结束前点位暂存在前端，结束后点位和数量禁止修改。
- 需要状态、事件或浏览器 API 的组件明确使用客户端组件边界。当前首页使用 `"use client"`。

## API 与登录

- 前端通过 HTTP 使用后端接口，不直接访问 SQLite，也不在前端保存数据库访问逻辑。
- 登录提交 JSON `{username, password}` 到 `POST /auth/login`；成功后保存用户视图状态并进入训练工作台。
- 页面初始化调用 `GET /auth/me` 恢复有效会话；401 时进入未登录状态。
- Dashboard 上半部分展示 username 和 name，右侧提供退出登录；退出成功后由首页清空用户并返回欢迎页。登录、注册及刷新恢复保持可用。
- 登录令牌由后端通过 HttpOnly Cookie 管理，不将其复制到 localStorage，也不尝试用 JavaScript 读取。
- API 请求集中在 `web/lib/api.js`，使用 `/api` 同源代理并携带凭据。`web/next.config.mjs` 的 `BACKEND_URL` 默认指向本地 8000；配置改变后需重启或重新构建前端，不额外开启 CORS。
- 不把密码、Cookie、令牌或敏感响应写入控制台或持久化存储。

## 训练与统计展示

- 严格执行职责边界：前端只负责页面切换、交互状态、表单输入和调用接口；训练业务规则及统计计算统一在后端执行。
- 禁止前端从逐球记录计算出手数、命中数、命中率、分区统计或按日期筛选汇总；不得重复实现后端统计规则。
- 本组统计调用 GET /sessions/shot-groups/{group_id}/summary，直接展示 attempts、made、field_goals。统计失败单独重试读取，不重复结束保存；不展示当日或整场总命中率。
- 允许数字输入转换、基础表单校验及展示格式化（如 `field_goals * 100` 和保留一位小数）；后端负责最终校验。不得以格式化为名重新计算统计。
- 实现创建训练、添加投篮、结束训练、训练列表、单场详情、总体与分区统计。
- 区域值与后端 `ShootingZone` 保持一致，可映射为中文标签；不自行添加未约定的区域值。
- API 的 `field_goals` 为 0～1，展示时乘以 100 并加 `%`；统一展示精度，原始值不改写。
- 累计命中率使用后端统计结果，不平均各场百分比。
- 表单处理输入、提交、加载、成功和错误状态；提交期间防止重复操作。
- 训练结束后禁用新增投篮操作，同时由后端进行最终状态校验。
- 列表、详情和统计均提供加载、空数据和失败状态；表单使用对应 label 和合适的按钮类型。

## 当前边界与检查

- 旧批量接口已删除，前端不再调用 addShootingBatch；结束本组通过 finish 接口提交 zone、attempts 和 made。

- Dashboard 的开始训练按钮打开 UserSessionsForm，不直接创建训练。场次页面可以创建训练、选择场次进入 SingleShootingForm；投篮组页面可创建和选择组，进行中表单可结束组，已结束组展示后端统计。各层通过 onBack 返回上一级。
- 现有脚本：在 `web/` 执行 `npm run dev`、`npm run build`、`npm run start`、`npm run lint`。
- 前端没有 package.json 测试脚本；独立请求模块验证使用 `node --test validation/api.test.mjs`（根目录）。lint 和 build 分别验证代码规范与构建，不能替代浏览器流程验证。原 `test/` 仍按用户要求忽略。
- 新增依赖需有具体用途，同步维护依赖清单和锁文件；不要无目的升级技术栈。
