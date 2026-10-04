"use client";

import { useEffect, useState } from "react";
import { getShotGroupSummary } from "../api/shotGroups";

// 已结束的组传入 groupId，未选择或进行中时传 null。
export default function useShotGroupSummary(groupId) {
  const [result, setResult] = useState({ groupId: null, summary: null, loading: false, error: "" });
  const [reload, setReload] = useState(0);

  // 统计完全使用后端结果，切换组或离开页面时取消请求。
  useEffect(() => {
    if (!groupId) return;
    const controller = new AbortController();

    async function loadSummary() {
      setResult({ groupId, summary: null, loading: true, error: "" });
      try {
        const summary = await getShotGroupSummary(groupId, controller.signal);
        if (!controller.signal.aborted) {
          setResult({ groupId, summary, loading: false, error: "" });
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setResult({ groupId, summary: null, loading: false, error: error.message });
        }
      }
    }

    loadSummary();
    return () => controller.abort();
  }, [groupId, reload]);

  function refreshSummary() {
    setReload((value) => value + 1);
  }

  const summary = result.groupId === groupId ? result.summary : null;
  const error = result.groupId === groupId ? result.error : "";
  const loading = Boolean(groupId) && (result.groupId !== groupId || result.loading);

  return { summary, loading, error, refreshSummary };
}
