import { useState } from "react";
import { loginUser } from "@/lib/api";

export default function LoginForm({ onBack, onLogin, initialUsername = "", notice = "" }) {
  const [username, setUsername] = useState(initialUsername);
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError("");
    try {
      const user = await loginUser({ username, password });
      setPassword("");
      onLogin(user);
    } catch (error) {
      setError(error.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <main>
      <h1>登录</h1>
      {notice && <p role="status">{notice}</p>}
      <form onSubmit={handleSubmit} aria-busy={pending}>
        <fieldset disabled={pending}>
          <label htmlFor="login-username">用户名</label>
          <input id="login-username" name="username" autoComplete="username" required maxLength={50}
            value={username} onChange={(event) => setUsername(event.target.value)} />
          <label htmlFor="login-password">密码</label>
          <input id="login-password" name="password" type="password" autoComplete="current-password" required minLength={8}
            value={password} onChange={(event) => setPassword(event.target.value)} />
          <button type="submit">{pending ? "登录中…" : "登录"}</button>
          <button type="button" onClick={onBack}>返回首页</button>
        </fieldset>
        {error && <p role="alert">{error}</p>}
      </form>
    </main>
  );
}
