"use client";

import { useEffect, useRef, useState } from "react";
import { createShootingSession, getShootingSessions } from "../api/userSessions";

// 管理用户的训练场次、当前选择和返回列表。
export default function useUserSessions(userId) {
  const [list, setList] = useState({ userId: null, sessions: [], loading: false, error: "" });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [reload, setReload] = useState(0);
  const [selection, setSelection] = useState(null);
  const busy = useRef(false);

  // 切换用户或离开页面时取消旧请求。
  useEffect(() => {
    if (!userId) return;
    const controller = new AbortController();

    async function loadSessions() {
      setList({ userId, sessions: [], loading: true, error: "" });
      try {
        const sessions = await getShootingSessions(userId, controller.signal);
        if (!controller.signal.aborted) {
          setList({ userId, sessions, loading: false, error: "" });
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setList({ userId, sessions: [], loading: false, error: error.message });
        }
      }
    }

    loadSessions();
    return () => controller.abort();
  }, [userId, reload]);

  const loading = Boolean(userId) && (list.userId !== userId || list.loading);
  const sessions = list.userId === userId ? list.sessions : [];
  const error = list.userId === userId ? list.error : "";
  const selectedSession = selection?.user_id === userId ? selection : null;

  function openSession(session) {
    if (session.user_id === userId) setSelection(session);
  }

  // 后续作为 SingleShootingForm 的 onBack，返回场次列表。
  function backToSessions() {
    setSelection(null);
  }

  // 新建整场训练，成功加入列表；失败不改变已有场次。
  async function createSession() {
    if (busy.current || loading) return null;
    if (!userId) {
      setCreateError("请先登录");
      return null;
    }
    busy.current = true;
    setCreating(true);
    setCreateError("");
    try {
      const session = await createShootingSession(userId);
      setList((current) => current.userId === userId
        ? { ...current, sessions: [...current.sessions, session] }
        : current);
      return session;
    } catch (error) {
      setCreateError(error.message);
      return null;
    } finally {
      busy.current = false;
      setCreating(false);
    }
  }

  function refreshSessions() {
    if (!busy.current) setReload((value) => value + 1);
  }

  return {
    sessions, loading, error, creating, createError, createSession, refreshSessions,
    selectedSession, openSession, backToSessions,
  };
}
