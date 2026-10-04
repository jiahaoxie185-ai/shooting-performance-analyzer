import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

// 以 ESM 加载现有模块，不修改前端的模块配置。
async function loadModule(path) {
  const source = await readFile(new URL(path, import.meta.url), "utf8");
  return import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
}

const api = await loadModule("../web/lib/api.js");

test("投篮组创建、查询和结束请求使用正确接口", async (t) => {
  const calls = [];
  t.mock.method(globalThis, "fetch", async (url, options) => {
    calls.push({ url, options });
    return Response.json({ id: "group-a", shots: [] });
  });
  await api.createShootingSession("user-a");
  await api.createShotGroup("session-a");
  const signal = new AbortController().signal;
  await api.getShotGroup("group-a", signal);
  await api.finishShotGroup("group-a", { zone: "top_three", attempts: 20, made: 14 });
  await api.getShotGroupSummary("group-a", signal);
  assert.deepEqual(calls.map(({ url }) => url), [
    "/api/sessions", "/api/sessions/session-a/shot-groups",
    "/api/sessions/shot-groups/group-a", "/api/sessions/shot-groups/group-a/finish",
    "/api/sessions/shot-groups/group-a/summary",
  ]);
  assert.deepEqual(JSON.parse(calls[1].options.body), {});
  assert.deepEqual(JSON.parse(calls[3].options.body), { zone: "top_three", attempts: 20, made: 14 });
  assert.ok(calls.every(({ options }) => options.credentials === "include"));
  assert.equal(calls[2].options.cache, "no-store");
  assert.equal(calls[2].options.signal, signal);
  assert.equal(calls[4].options.cache, "no-store");
  assert.equal(calls[4].options.signal, signal);
});

test("训练与组列表读取不缓存且支持取消", async (t) => {
  const calls = [];
  const signal = new AbortController().signal;
  t.mock.method(globalThis, "fetch", async (url, options) => {
    calls.push({ url, options });
    return Response.json([]);
  });
  await api.getShootingSessions("user-a", signal);
  await api.getShotGroups("session-a", signal);
  assert.deepEqual(calls.map(({ url }) => url), [
    "/api/sessions/users/user-a", "/api/sessions/session-a/shot-groups",
  ]);
  assert.ok(calls.every(({ options }) => options.cache === "no-store" && options.signal === signal));
});

// 统计结果保持后端口径，前端请求模块不重算或改写数值。
test("本组统计保留后端结果，失败后可以单独重新查询", async (t) => {
  const summary = { attempts: 20, made: 14, field_goals: 0.7, zones: {} };
  let failed = true;
  t.mock.method(globalThis, "fetch", async () => {
    if (failed) return Response.json({ detail: "统计暂不可用" }, { status: 503 });
    return Response.json(summary);
  });
  await assert.rejects(api.getShotGroupSummary("group-a"), { status: 503 });
  failed = false;
  assert.deepEqual(await api.getShotGroupSummary("group-a"), summary);
});
