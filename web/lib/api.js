export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function errorMessage(detail, status) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const fields = { username: "用户名", name: "姓名", password: "密码", attempts: "出手数", made: "命中数", zone: "投篮区域" };
    return detail.map((item) => {
      const field = item.loc?.at(-1);
      return `${fields[field] || field || "输入"}：${item.msg || "格式不正确"}`;
    }).join("；");
  }
  return `请求失败（${status}），请稍后重试`;
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      credentials: "include",
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new ApiError("无法连接服务，请检查网络后重试", 0);
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(errorMessage(data?.detail, response.status), response.status);
  if (data === null) throw new ApiError("服务返回了无效响应，请稍后重试", response.status);
  return data;
}

export function registerUser({ username, name, password }) {
  return request("/users", { method: "POST", body: JSON.stringify({ username, name, password }) });
}

export function loginUser({ username, password }) {
  return request("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
}

export function getCurrentUser(signal) {
  return request("/auth/me", { cache: "no-store", signal });
}

export function logoutUser() {
  return request("/auth/logout", { method: "POST" });
}

export function createShootingSession(userId) {
  return request("/sessions", { method: "POST", body: JSON.stringify({ user_id: userId }) });
}

export function getShootingSessions(userId, signal) {
  return request(`/sessions/users/${userId}`, { cache: "no-store", signal });
}

export function getShootingSession(sessionId) {
  return request(`/sessions/${sessionId}`, { cache: "no-store" });
}

export function addShootingBatch(sessionId, { attempts, made, zone }) {
  return request(`/sessions/${sessionId}/shots/batch`, {
    method: "POST", body: JSON.stringify({ attempts, made, zone }),
  });
}

export function finishShootingSession(sessionId) {
  return request(`/sessions/${sessionId}/finish`, { method: "POST" });
}
