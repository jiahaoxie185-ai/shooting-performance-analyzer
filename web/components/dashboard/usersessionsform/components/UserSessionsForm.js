"use client";

import useUserSessions from "../hooks/useUserSessions";
import SingleShootingForm from "../../singleshootingform/components/SingleShootingForm";
import styles from "../../Dashboard.module.css";

// 场次状态由 hook 管理，组件负责列表和详情的展示。
export default function UserSessionsForm({ userId, onBack }) {
  const {
    sessions, loading, error, creating, createError, createSession, refreshSessions,
    selectedSession, openSession, backToSessions,
  } = useUserSessions(userId);

  // 选择场次后展示其投篮组，返回时清空场次选择。
  if (selectedSession) {
    return (
      <SingleShootingForm
        key={selectedSession.id} sessionId={selectedSession.id} onBack={backToSessions}
      />
    );
  }

  return (
    <section className={styles.card}>
      <div className={styles.header}>
        <h2>我的训练场次</h2>
        <button type="button" onClick={createSession} disabled={!userId || loading || creating}>
          {creating ? "创建中…" : "创建训练"}
        </button>
      </div>
      {!userId && <p>请先登录</p>}
      {loading && <p role="status">正在读取训练场次…</p>}
      {error && (
        <div>
          <p className={styles.error} role="alert">{error}</p>
          <button type="button" onClick={refreshSessions} disabled={creating}>重新读取列表</button>
        </div>
      )}
      {createError && <p className={styles.error} role="alert">{createError}</p>}
      {userId && !loading && !error && sessions.length === 0 && <p>还没有训练场次</p>}
      {!loading && !error && (
        <ul className={styles.sessions}>
          {sessions.map((session) => (
            <li key={session.id}>
              <button type="button" onClick={() => openSession(session)} disabled={creating}>
                <span>{session.started_at.replace("T", " ")}</span>
                <span>{session.ended_at ? "已结束" : "进行中"} · 查看投篮组 →</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {/* 返回 Dashboard，与场次详情返回列表分开。 */}
      {onBack && <button type="button" onClick={onBack} disabled={creating}>返回工作台</button>}
    </section>
  );
}
