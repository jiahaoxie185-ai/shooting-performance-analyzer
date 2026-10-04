"use client";

import { useRef, useState } from "react";
import { logoutUser } from "./api";

// 管理 Dashboard 页面切换和退出登录，场次内部状态由子页面管理。
export default function useDashboard(onLogout) {
  const [sessionsOpen, setSessionsOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const busy = useRef(false);

  function openSessions() {
    if (!busy.current) setSessionsOpen(true);
  }

  // 作为 UserSessionsForm 的 onBack，返回 Dashboard。
  function backToDashboard() {
    if (!busy.current) setSessionsOpen(false);
  }

  async function handleLogout() {
    if (busy.current) return false;
    busy.current = true;
    setLoggingOut(true);
    setLogoutError("");
    try {
      await logoutUser();
    } catch (error) {
      // 退出失败保留当前页面，用户可以重试。
      setLogoutError(error.message);
      return false;
    } finally {
      busy.current = false;
      setLoggingOut(false);
    }
    setSessionsOpen(false);
    // 成功后通知上层清空用户状态，并返回欢迎页。
    onLogout?.();
    return true;
  }

  return { sessionsOpen, openSessions, backToDashboard, loggingOut, logoutError, handleLogout };
}
