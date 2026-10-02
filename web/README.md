# 投篮训练 Web

已实现注册、登录、Cookie 会话恢复和退出。注册成功后进入登录页；登录后工作台显示真实用户信息，训练区暂为占位。

## 本地启动

在仓库根目录，使用已有 Python 环境初始化缺失表并启动后端：

```bash
.venv/bin/python -m infrastructure.init_db
.venv/bin/python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

初始化会写入根目录 `basketball.db`，不会迁移已有表结构。仓库尚未声明后端依赖清单，上述命令依赖当前已有虚拟环境。

另开终端启动前端：

```bash
cd web
npm ci
npm run dev
```

浏览器访问 `http://localhost:3000`。`web/next.config.mjs` 将 `/api` 代理到 `BACKEND_URL`（默认 `http://127.0.0.1:8000`），无需浏览器直接跨域请求。改变 `BACKEND_URL` 后重启或重新构建前端。

Cookie 是 HttpOnly、SameSite=Lax、Path=/，有效期 7 天；令牌不保存在 localStorage。生产 HTTPS 为后端设置 `COOKIE_SECURE=true`，并配置前端构建时的 `BACKEND_URL`；生产部署尚未验证。

## 验证

在仓库根目录：

```bash
.venv/bin/python -B -m unittest validation.auth_flow -v
node --test validation/api.test.mjs
```

认证验证使用临时 SQLite，不写入真实数据库，不使用现有 `test/`。在 `web/` 执行 `npm run lint`、`npm run build`；构建成功后可执行 `npm run start`。

---

以下为 Next.js 原始框架说明。

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.js`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
