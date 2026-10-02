"use client";

import { useEffect, useRef, useState } from "react";
import {
  addShootingBatch, createShootingSession, finishShootingSession,
  getShootingSession, getShootingSessions, logoutUser,
} from "@/lib/api";
import { SHOOTING_ZONES, summarizeShots, summarizeToday } from "@/lib/shooting";
import styles from "./Dashboard.module.css";

export default function Dashboard({ user, onLogout }) {
  const [sessions, setSessions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [reload, setReload] = useState(0);
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [zone, setZone] = useState("paint");
  const [attempts, setAttempts] = useState("");
  const [made, setMade] = useState("");
  const busy = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    getShootingSessions(user.id, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setSessions(data);
      })
      .catch((error) => {
        if (!controller.signal.aborted) setListError(error.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [user.id, reload]);

  async function run(action, operation) {
    if (busy.current) return;
    busy.current = true;
    setPending(action);
    setError("");
    setNotice("");
    try {
      await operation();
    } catch (error) {
      setError(error.message);
    } finally {
      busy.current = false;
      setPending("");
    }
  }

  function updateSession(session) {
    setSelected(session);
    setSessions((items) => [session, ...items.filter((item) => item.id !== session.id)]);
  }

  function resetForm() {
    setZone("paint");
    setAttempts("");
    setMade("");
  }

  function handleCreate() {
    run("create", async () => {
      updateSession(await createShootingSession(user.id));
      resetForm();
    });
  }

  function handleOpen(id) {
    run("open", async () => {
      updateSession(await getShootingSession(id));
      resetForm();
    });
  }

  function handleAdd(event) {
    event.preventDefault();
    if (busy.current || selected.ended_at) return;
    const attemptCount = Number(attempts);
    const madeCount = Number(made);
    if (!attempts.trim() || !made.trim() || !Number.isSafeInteger(attemptCount)
      || !Number.isSafeInteger(madeCount) || attemptCount <= 0
      || madeCount < 0 || madeCount > attemptCount) {
      setNotice("");
      setError("请输入整数：出手数大于 0，命中数在 0 和出手数之间。");
      return;
    }
    run("add", async () => {
      updateSession(await addShootingBatch(selected.id, { attempts: attemptCount, made: madeCount, zone }));
      setAttempts("");
      setMade("");
      setNotice(`已添加 ${attemptCount} 次出手，其中命中 ${madeCount} 球。`);
    });
  }

  function handleFinish() {
    run("finish", async () => {
      updateSession(await finishShootingSession(selected.id));
      setAttempts("");
      setMade("");
      setNotice("训练已结束。");
    });
  }

  function handleBack() {
    setSelected(null);
    setError("");
    setNotice("");
    resetForm();
  }

  const disabled = Boolean(pending);
  const summary = selected ? summarizeShots(selected.shots) : null;
  const today = summarizeToday(sessions);
  const orderedSessions = [...sessions].sort((a, b) => new Date(b.started_at) - new Date(a.started_at));

  return (
    <main className={styles.dashboard}>
      <header className={styles.header}>
        <div><h1>训练工作台</h1><p>{user.name} · {user.username}</p></div>
        <button type="button" disabled={disabled} onClick={() => run("logout", async () => {
          await logoutUser();
          onLogout();
        })}>{pending === "logout" ? "退出中…" : "退出登录"}</button>
      </header>
      {error && <p className={styles.error} role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}

      {!selected ? (
        <section className={styles.card} aria-label="单次训练">
          <div className={styles.header}>
            <h2>单次训练</h2>
            <button type="button" disabled={disabled || loading || Boolean(listError)} onClick={handleCreate}>
              {pending === "create" ? "创建中…" : "创建训练"}
            </button>
          </div>
          {loading ? <p role="status">正在加载训练…</p> : listError ? (
            <div><p role="alert">{listError}</p><button type="button" disabled={disabled} onClick={() => {
              setListError("");
              setLoading(true);
              setReload((value) => value + 1);
            }}>重新加载</button></div>
          ) : orderedSessions.length === 0 ? <p>还没有训练，点击“创建训练”开始。</p> : (
            <ul className={styles.sessions}>
              {orderedSessions.map((session) => (
                <li key={session.id}>
                  <button type="button" disabled={disabled} onClick={() => handleOpen(session.id)}>
                    <span>{new Date(session.started_at).toLocaleString("zh-CN")}</span>
                    <span>{session.ended_at ? "已结束" : "进行中"} · {session.shots.length} 次出手 · 查看训练 →</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {pending === "open" && <p role="status">正在打开训练…</p>}
        </section>
      ) : (
        <>
          <section className={styles.card} aria-label="训练详情">
            <div className={styles.header}>
              <h2>单次训练 · {selected.ended_at ? "已结束" : "进行中"}</h2>
              <button type="button" disabled={disabled} onClick={handleBack}>返回训练列表</button>
            </div>
            <p>开始时间：{new Date(selected.started_at).toLocaleString("zh-CN")}</p>
            <p>本场出手 {summary.attempts} 次，命中 {summary.made} 球，命中率 {summary.percentage.toFixed(1)}%</p>
            {!selected.ended_at ? (
              <>
                <form onSubmit={handleAdd}>
                  <fieldset className={styles.form} disabled={disabled}>
                    <label htmlFor="shooting-zone">投篮区域</label>
                    <select id="shooting-zone" value={zone} onChange={(event) => setZone(event.target.value)}>
                      {SHOOTING_ZONES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                    <label htmlFor="shooting-attempts">出手数（投篮数）</label>
                    <input id="shooting-attempts" type="number" min="1" step="1" required value={attempts}
                      onChange={(event) => setAttempts(event.target.value)} placeholder="例如：20" />
                    <label htmlFor="shooting-made">命中数</label>
                    <input id="shooting-made" type="number" min="0" step="1" required
                      max={attempts || undefined} value={made} onChange={(event) => setMade(event.target.value)} placeholder="例如：14" />
                    <p>填写本次追加的数量，可以分多批添加。</p>
                    <button type="submit">{pending === "add" ? "添加中…" : "添加"}</button>
                  </fieldset>
                </form>
                <button type="button" disabled={disabled} onClick={handleFinish}>
                  {pending === "finish" ? "结束中…" : "结束训练"}
                </button>
              </>
            ) : <p>结束时间：{new Date(selected.ended_at).toLocaleString("zh-CN")} · 已停止录入</p>}
          </section>
          {selected.ended_at && (
            <section className={styles.card} aria-label="今日命中率">
              <h2>今日命中率</h2>
              <p className={styles.percentage}>{today.percentage.toFixed(1)}%</p>
              <p>今日出手 {today.attempts} 次，命中 {today.made} 球。</p>
              <p>按本地日期汇总所有训练中今日录入的投篮。</p>
            </section>
          )}
        </>
      )}
    </main>
  );
}
