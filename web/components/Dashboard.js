import { useState } from "react";
import { logoutUser } from "@/lib/api";

export default function Dashboard({ user, onLogout }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function handleLogout() {
    if (pending) return;
    setPending(true);
    setError("");
    try {
      await logoutUser();
      onLogout();
    } catch (error) {
      setError(error.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <main>
      <h1>训练工作台</h1>
      <section aria-label="当前用户">
        <p>姓名：{user.name}</p>
        <p>用户名：{user.username}</p>
        <p>用户 ID：{user.id}</p>
        <button type="button" onClick={handleLogout} disabled={pending}>{pending ? "退出中…" : "退出登录"}</button>
        {error && <p role="alert">{error}</p>}
      </section>
      <section><h3>创建单次投篮场次</h3></section>
      <section><h3>添加投篮</h3></section>
      <section><h3>单次投篮场次总结</h3></section>
      <section><h3>全部投篮训练场次</h3></section>
      <section><h3>总命中率</h3></section>
    </main>
  );
}
