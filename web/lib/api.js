// 所有请求通过同源代理发送，统计交给后端计算。
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options, credentials: "include",
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new ApiError("无法连接服务，请检查网络后重试", 0);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const fields = { username: "用户名", name: "姓名", password: "密码", attempts: "出手数", made: "命中数", zone: "投篮区域" };
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((item) => `${fields[item.loc?.at(-1)] || item.loc?.at(-1) || "输入"}：${item.msg}`).join("；")
      : `请求失败（${response.status}）`;
    throw new ApiError(message, response.status);
  }
  if (data === null) throw new ApiError("服务返回了无效响应，请稍后重试", response.status);
  return data;
}

// 保持已有登录、注册和刷新恢复功能。
export function registerUser({ username, name, password }) {
  return request("/users", { method: "POST", body: JSON.stringify({ username, name, password }) });
}
export function loginUser({ username, password }) {
  return request("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
}
export function getCurrentUser(signal) {
  return request("/auth/me", { cache: "no-store", signal });
}

// 先创建所属训练，再在该训练下创建投篮组。
export function createShootingSession(userId) {
  return request("/sessions", { method: "POST", body: JSON.stringify({ user_id: userId }) });
}
export function getShootingSessions(userId, signal) {
  return request(`/sessions/users/${userId}`, { cache: "no-store", signal });
}
export function getShotGroups(sessionId, signal) {
  return request(`/sessions/${sessionId}/shot-groups`, { cache: "no-store", signal });
}
export function createShotGroup(sessionId) {
  return request(`/sessions/${sessionId}/shot-groups`, { method: "POST", body: JSON.stringify({}) });
}
export function getShotGroup(groupId, signal) {
  return request(`/sessions/shot-groups/${groupId}`, { cache: "no-store", signal });
}
export function finishShotGroup(groupId, { zone, attempts, made }) {
  return request(`/sessions/shot-groups/${groupId}/finish`, {
    method: "POST", body: JSON.stringify({ zone, attempts, made }),
  });
}
export function getShotGroupSummary(groupId, signal) {
  return request(`/sessions/shot-groups/${groupId}/summary`, { cache: "no-store", signal });
}
