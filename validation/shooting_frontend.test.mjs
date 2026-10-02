import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

async function loadModule(path) {
  const source = await readFile(new URL(path, import.meta.url), "utf8");
  return import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
}

const { summarizeToday, summarizeShots } = await loadModule("../web/lib/shooting.js");
const api = await loadModule("../web/lib/api.js");

test("今日统计按投篮日期筛选并合并数量，不平均各场命中率", () => {
  const now = new Date(2026, 9, 2, 12);
  const shot = (made, date = "2026-10-02T10:00:00") => ({ made, attempted_at: date });
  const sessions = [
    { shots: [shot(true)] },
    { shots: [shot(false), shot(false), shot(false), shot(true, "2026-10-01T23:59:59")] },
    { shots: [shot(true, "2026-10-03T00:00:00")] },
    { shots: [] },
  ];
  assert.deepEqual(summarizeToday(sessions, now), { attempts: 4, made: 1, percentage: 25 });
  assert.deepEqual(summarizeToday([], now), { attempts: 0, made: 0, percentage: 0 });
  assert.equal(summarizeShots(Array.from({ length: 20 }, (_, i) => shot(i < 14))).percentage, 70);
});

test("训练请求连接正确接口，批量数量作为数字传输", async (t) => {
  const calls = [];
  t.mock.method(globalThis, "fetch", async (url, options) => {
    calls.push({ url, options });
    return Response.json({ id: "session-a", shots: [] });
  });
  await api.createShootingSession("user-a");
  await api.getShootingSessions("user-a");
  await api.getShootingSession("session-a");
  await api.addShootingBatch("session-a", { attempts: 20, made: 14, zone: "top_three" });
  await api.finishShootingSession("session-a");
  assert.deepEqual(calls.map(({ url }) => url), [
    "/api/sessions", "/api/sessions/users/user-a", "/api/sessions/session-a",
    "/api/sessions/session-a/shots/batch", "/api/sessions/session-a/finish",
  ]);
  assert.deepEqual(JSON.parse(calls[3].options.body), { attempts: 20, made: 14, zone: "top_three" });
  assert.deepEqual(calls.map(({ options }) => options.method || "GET"), ["POST", "GET", "GET", "POST", "POST"]);
  assert.ok(calls.every(({ options }) => options.credentials === "include"));
  assert.equal(calls[1].options.cache, "no-store");
  assert.equal(calls[2].options.cache, "no-store");
});
