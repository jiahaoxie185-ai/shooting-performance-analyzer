"use client";

import { useRef, useState } from "react";
import { finishShotGroup } from "../api/shotGroups";

// 管理提交状态；区域和数量输入由进行中表单保存。
export default function useFinishShotGroup(groupId) {
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState({ groupId: null, group: null, error: "" });
  const busy = useRef(false);

  // 成功返回已结束的组；失败返回 null，不清空表单输入。
  async function finishGroup({ zone, attempts, made }) {
    if (busy.current) return null;
    if (!groupId) {
      setResult({ groupId, group: null, error: "请先选择一个投篮组" });
      return null;
    }
    busy.current = true;
    setPending(true);
    setResult({ groupId, group: null, error: "" });
    try {
      const group = await finishShotGroup(groupId, { zone, attempts, made });
      setResult({ groupId, group, error: "" });
      return group;
    } catch (error) {
      setResult({ groupId, group: null, error: error.message });
      return null;
    } finally {
      busy.current = false;
      setPending(false);
    }
  }

  const group = result.groupId === groupId ? result.group : null;
  const error = result.groupId === groupId ? result.error : "";

  return { pending, error, group, finishGroup };
}
