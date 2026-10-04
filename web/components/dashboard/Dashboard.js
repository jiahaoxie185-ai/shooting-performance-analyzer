"use client";

import useDashboard from "./hook";
import UserSessionsForm from "./usersessionsform/components/UserSessionsForm";
import styles from "./Dashboard.module.css";

// 用户信息由首页传入，页面切换和退出操作由 hook 管理。
export default function Dashboard({ user, onLogout }) {
  const {
    sessionsOpen, openSessions, backToDashboard, loggingOut, logoutError, handleLogout,
  } = useDashboard(onLogout);

  return (
    <main className={styles.dashboard}>
      <header className={`${styles.card} ${styles.header}`}>
        <div>
          <h1>训练工作台</h1>
          <p>用户名：{user.username}</p>
          <p>姓名：{user.name}</p>
        </div>
        <button type="button" onClick={handleLogout} disabled={loggingOut}>
          {loggingOut ? "退出中…" : "退出登录"}
        </button>
      </header>
      {logoutError && <p className={styles.error} role="alert">{logoutError}</p>}

      {/* 开始训练只打开场次页面，不直接创建新场次。 */}
      {sessionsOpen ? (
        <UserSessionsForm userId={user.id} onBack={backToDashboard} />
      ) : (
        <section className={styles.card}>
          <button type="button" onClick={openSessions} disabled={loggingOut}>开始训练</button>
        </section>
      )}
    </main>
  );
}
