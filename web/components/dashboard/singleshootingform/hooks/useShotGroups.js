"use client";

import { useEffect, useRef, useState } from "react";
import { createShotGroup, getShotGroups } from "../api/shotGroups";

// 管理指定训练的组列表、当前选择和返回列表。
export default function useShotGroups(sessionId) {
  const [list, setList] = useState({ sessionId: null, groups: [], loading: false, error: "" });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [reload, setReload] = useState(0);
  const [selection, setSelection] = useState(null);
  const busy = useRef(false);

  // 离开页面或切换训练时，取消旧列表请求。
  useEffect(() => {
    if (!sessionId) return;
    const controller = new AbortController();

    async function loadGroups() {
      setList({ sessionId, groups: [], loading: true, error: "" });
      try {
        const groups = await getShotGroups(sessionId, controller.signal);
        if (!controller.signal.aborted) {
          setList({ sessionId, groups, loading: false, error: "" });
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setList({ sessionId, groups: [], loading: false, error: error.message });
        }
      }
    }

    loadGroups();
    return () => controller.abort();
  }, [sessionId, reload]);

  const loading = Boolean(sessionId) && (list.sessionId !== sessionId || list.loading);
  const groups = list.sessionId === sessionId ? list.groups : [];
  const error = list.sessionId === sessionId ? list.error : "";
  // 切换训练后，不展示上一场选中的组。
  const selectedGroup = selection?.session_id === sessionId ? selection : null;

  function openGroup(group) {
    if (group.session_id === sessionId) setSelection(group);
  }

  function backToList() {
    setSelection(null);
  }

  // 创建成功返回后端的组对象；失败返回 null，页面可保留输入。
  async function createGroup() {
    if (busy.current || loading) return null;
    if (!sessionId) {
      setCreateError("请先选择一场训练");
      return null;
    }
    busy.current = true;
    setCreating(true);
    setCreateError("");
    try {
      const group = await createShotGroup(sessionId);
      setList((current) => current.sessionId === sessionId
        ? { ...current, groups: [...current.groups, group] }
        : current);
      return group;
    } catch (error) {
      setCreateError(error.message);
      return null;
    } finally {
      busy.current = false;
      setCreating(false);
    }
  }

  // 结束组后更新列表状态，无需重新计算任何统计。
  function updateGroup(group) {
    setList((current) => current.sessionId === group.session_id
      ? { ...current, groups: current.groups.map((item) => item.id === group.id ? group : item) }
      : current);
    // 保存成功后同步当前组，父组件即可展示结束统计。
    setSelection((current) => current?.id === group.id ? group : current);
  }

  function refreshGroups() {
    if (!busy.current) setReload((value) => value + 1);
  }

  return {
    groups, loading, error, creating, createError, createGroup, updateGroup, refreshGroups,
    selectedGroup, openGroup, backToList,
  };
}
