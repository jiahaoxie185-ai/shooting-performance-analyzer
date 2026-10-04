"use client";

import { useEffect, useState } from "react";
import Welcome from "@/components/Welcome";
import LoginForm from "@/components/LoginForm";
import RegisterForm from "@/components/RegisterForm";
import Dashboard from "@/components/dashboard/Dashboard";
import { getCurrentUser } from "@/lib/api";

export default function Home() {
  const [screen, setScreen] = useState("welcome");
  const [currentUser, setCurrentUser] = useState(null);
  const [restoring, setRestoring] = useState(true);
  const [restoreError, setRestoreError] = useState("");
  const [restoreAttempt, setRestoreAttempt] = useState(0);
  const [registeredUsername, setRegisteredUsername] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    getCurrentUser(controller.signal)
      .then((user) => {
        if (controller.signal.aborted) return;
        setCurrentUser(user);
        setScreen("dashboard");
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        setCurrentUser(null);
        setScreen("welcome");
        if (error.status !== 401) setRestoreError(error.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setRestoring(false);
      });
    return () => controller.abort();
  }, [restoreAttempt]);

  function retryRestore() {
    setRestoreError("");
    setRestoring(true);
    setRestoreAttempt((attempt) => attempt + 1);
  }

  if (restoring) return <main><p role="status">正在恢复登录状态…</p></main>;
  if (restoreError) {
    return <main><p role="alert">{restoreError}</p><button type="button" onClick={retryRestore}>重试恢复登录</button></main>;
  }
  if (screen === "login") {
    return <LoginForm onBack={() => setScreen("welcome")} initialUsername={registeredUsername}
      notice={registeredUsername ? "注册成功，请使用新账号登录" : ""}
      onLogin={(user) => {
        setCurrentUser(user);
        setRegisteredUsername("");
        setScreen("dashboard");
      }} />;
  }
  if (screen === "register") {
    return <RegisterForm onBack={() => setScreen("welcome")} onRegistered={(user) => {
      setRegisteredUsername(user.username);
      setScreen("login");
    }} />;
  }
  if (screen === "dashboard" && currentUser) {
    return <Dashboard user={currentUser} onLogout={() => {
      // 后端退出成功后，清空用户并展示欢迎页。
      setCurrentUser(null);
      setRegisteredUsername("");
      setScreen("welcome");
    }} />;
  }
  return <Welcome onLogin={() => setScreen("login")} onRegister={() => {
    setRegisteredUsername("");
    setScreen("register");
  }} />;
}
