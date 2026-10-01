"use client"

import { useState } from "react";
import Welcome from "@/components/Welcome";
import LoginForm from "@/components/LoginForm";
import RegisterForm from "@/components/RegisterForm";
import Dashboard from "@/components/Dashboard";


// 首页：根据 screen 状态切换欢迎、登录、注册和训练工作台视图。
export default function Home() {
  // 当前显示的视图，默认显示欢迎页。
  const [screen, setScreen] = useState("welcome");

  if (screen === "login") {
    return <LoginForm onBack={() => setScreen("welcome")} />;
  }

  if (screen === "register") {
    return <RegisterForm onBack={() => setScreen("welcome")} />;
  }

  if (screen === "dashboard") {
    return <Dashboard />;
  }

  return (
  <Welcome
  onLogin={() => setScreen("login")}
  onRegister={() => setScreen("register")}
  />
)

}
