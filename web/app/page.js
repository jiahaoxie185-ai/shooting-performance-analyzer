"use client"

import { useState } from "react";
import Welcome from "@/components/Welcome";
import LoginForm from "@/components/LoginForm";
import RegisterFrom from "@/components/RegisterForm";
import Dashboard from "@/components/Dashboard";


export default function Home() {
  const [screen, setScreen] = useState("welcome");

  if (screen === "login") {
    return <LoginForm onBack={() => setScreen("welcome")} />;
  }

  if (screen === "register") {
    return <RegisterFrom onBack={() => setScreen("welcome")} />;
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
