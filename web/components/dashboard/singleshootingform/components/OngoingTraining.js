"use client";

import { useId } from "react";
import { SHOOTING_ZONES } from "../../../../lib/shooting";
import useOngoingTraining from "../hooks/useOngoingTraining";
import styles from "../../Dashboard.module.css";

// 父组件传入组 ID、返回操作和保存成功后的页面切换操作。
// 切换组时使用 key={groupId}，让不同组拥有独立的输入状态。
export default function OngoingTraining({ groupId, onBack, onFinished }) {
  const id = useId();
  const {
    zone, setZone, attempts, setAttempts, made, setMade,
    pending, error, finished, handleSubmit,
  } = useOngoingTraining(groupId, onFinished);

  return (
    <section className={styles.card}>
      <h2>进行中的投篮组</h2>
      <form onSubmit={handleSubmit} aria-busy={pending}>
        {/* 保存期间和保存成功后，禁止继续修改输入。 */}
        <fieldset className={styles.form} disabled={pending || finished || !groupId}>
          <label htmlFor={`${id}-zone`}>投篮点位</label>
          <select id={`${id}-zone`} value={zone} onChange={(event) => setZone(event.target.value)} required>
            <option value="">请选择点位</option>
            {SHOOTING_ZONES.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>

          <label htmlFor={`${id}-attempts`}>出手数</label>
          <input
            id={`${id}-attempts`} type="number" min="1" step="1" required
            value={attempts} onChange={(event) => setAttempts(event.target.value)}
          />

          <label htmlFor={`${id}-made`}>命中数</label>
          <input
            id={`${id}-made`} type="number" min="0" step="1" required
            value={made} onChange={(event) => setMade(event.target.value)}
          />

          <button type="submit">{pending ? "保存中…" : "结束本组"}</button>
        </fieldset>
        {(!groupId || error) && (
          <p className={styles.error} role="alert">{!groupId ? "请先选择一个投篮组" : error}</p>
        )}
        {finished && <p role="status">本组已保存</p>}
        {/* 返回只切换页面，不提交表单。 */}
        <button type="button" onClick={onBack} disabled={pending || !onBack}>返回投篮组列表</button>
      </form>
    </section>
  );
}
