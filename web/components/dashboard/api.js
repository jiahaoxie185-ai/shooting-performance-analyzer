import { request } from "../../lib/api";

// 退出时由后端撤销会话并清除 Cookie。
export function logoutUser() {
  return request("/auth/logout", { method: "POST" });
}
