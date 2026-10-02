import { useState } from "react";
import { registerUser } from "@/lib/api";

export default function RegisterForm({ onBack, onRegistered }) {
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError("");
    try {
      const user = await registerUser({ username, name, password });
      setPassword("");
      onRegistered(user);
    } catch (error) {
      setError(error.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <main>
      <h1>注册</h1>
      <form onSubmit={handleSubmit} aria-busy={pending}>
        <fieldset disabled={pending}>
          <label htmlFor="register-username">用户名</label>
          <input id="register-username" name="username" autoComplete="username" required maxLength={50}
            value={username} onChange={(event) => setUsername(event.target.value)} />
          <label htmlFor="register-name">姓名</label>
          <input id="register-name" name="name" autoComplete="name" required maxLength={100}
            value={name} onChange={(event) => setName(event.target.value)} />
          <label htmlFor="register-password">密码</label>
          <input id="register-password" name="password" type="password" autoComplete="new-password" required minLength={8}
            value={password} onChange={(event) => setPassword(event.target.value)} />
          <button type="submit">{pending ? "注册中…" : "注册"}</button>
          <button type="button" onClick={onBack}>返回首页</button>
        </fieldset>
        {error && <p role="alert">{error}</p>}
      </form>
    </main>
  );
}
