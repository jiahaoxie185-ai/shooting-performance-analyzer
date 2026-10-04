"use client";

import { useState } from "react";
import useFinishShotGroup from "./useFinishShotGroup";

// 保存表单输入，提交状态和请求交给结束投篮组的 hook。
export default function useOngoingTraining(groupId, onFinished) {
  const [zone, setZone] = useState("");
  const [attempts, setAttempts] = useState("");
  const [made, setMade] = useState("");
  const [inputError, setInputError] = useState("");
  const { pending, error, group, finishGroup } = useFinishShotGroup(groupId);

  async function handleSubmit(event) {
    event.preventDefault();
    if (pending || group) return;
    setInputError("");

    // 输入框保存字符串，提交前转换为整数；后端仍做最终校验。
    const attemptCount = Number(attempts);
    const madeCount = Number(made);
    if (!zone) {
      setInputError("请选择投篮点位");
      return;
    }
    if (attempts.trim() === "" || made.trim() === ""
        || !Number.isSafeInteger(attemptCount) || !Number.isSafeInteger(madeCount)
        || attemptCount <= 0 || madeCount < 0 || madeCount > attemptCount) {
      setInputError("出手数必须为正整数，命中数必须为零到出手数之间的整数");
      return;
    }

    const finishedGroup = await finishGroup({ zone, attempts: attemptCount, made: madeCount });
    // 失败保留输入，成功通知父组件更新列表并切换到结束统计。
    if (finishedGroup) onFinished?.(finishedGroup);
  }

  return {
    zone, setZone, attempts, setAttempts, made, setMade,
    pending, error: inputError || error, finished: Boolean(group), handleSubmit,
  };
}
