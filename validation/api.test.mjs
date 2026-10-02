import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

// 以 ESM 加载现有模块，无需改变 web/package.json 的模块配置。
const source = await readFile(new URL("../web/lib/api.js", import.meta.url), "utf8");
const api = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);

test("认证请求使用同源代理、携带凭据且恢复不缓存", async (t) => {
  const calls = [];
  t.mock.method(globalThis, "fetch", async (url, options) => {
    calls.push({ url, options });
    return Response.json({ id: "user-a", username: "player-a" });
  });
  const signal = new AbortController().signal;
  await api.registerUser({ username: "player-a", name: "玩家", password: "example-password" });
  await api.loginUser({ username: "player-a", password: "example-password" });
  await api.getCurrentUser(signal);
  await api.logoutUser();
  assert.deepEqual(calls.map((call) => call.url), ["/api/users", "/api/auth/login", "/api/auth/me", "/api/auth/logout"]);
  for (const { options } of calls) assert.equal(options.credentials, "include");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[1].options.method, "POST");
  assert.equal(calls[3].options.method, "POST");
  assert.equal(calls[2].options.cache, "no-store");
  assert.equal(calls[2].options.signal, signal);
  assert.deepEqual(JSON.parse(calls[1].options.body), { username: "player-a", password: "example-password" });
});

test("后端业务错误与字段校验错误保留状态并提供可展示消息", async (t) => {
  t.mock.method(globalThis, "fetch", async () => Response.json({ detail: "该用户已存在" }, { status: 409 }));
  await assert.rejects(api.registerUser({}), { name: "ApiError", status: 409, message: "该用户已存在" });
  globalThis.fetch = async () => Response.json({ detail: [{ loc: ["body", "password"], msg: "至少八位" }] }, { status: 422 });
  await assert.rejects(api.registerUser({}), { status: 422, message: "密码：至少八位" });
});

test("网络失败、无效响应与取消请求有明确行为", async (t) => {
  t.mock.method(globalThis, "fetch", async () => { throw new TypeError("offline"); });
  await assert.rejects(api.getCurrentUser(), { name: "ApiError", status: 0, message: "无法连接服务，请检查网络后重试" });
  globalThis.fetch = async () => new Response("not json", { status: 200 });
  await assert.rejects(api.getCurrentUser(), { name: "ApiError", status: 200 });
  const aborted = new DOMException("cancelled", "AbortError");
  globalThis.fetch = async () => { throw aborted; };
  await assert.rejects(api.getCurrentUser(), (error) => error === aborted);
});
