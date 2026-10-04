"use client";

import useShotGroupSummary from "../hooks/useShotGroupSummary";
import styles from "../../Dashboard.module.css";

// 统计状态由 hook 管理，返回操作由父组件传入。
export default function CompletedTrainingSummary({ groupId, onBack }) {
  const { summary, loading, error, refreshSummary } = useShotGroupSummary(groupId);

  return (
    <section className={styles.card} aria-busy={loading}>
      <h2>本组结束统计</h2>
      {!groupId && <p role="alert">请先选择一个已结束的投篮组</p>}
      {loading && <p role="status">正在读取统计…</p>}
      {error && (
        <div>
          <p className={styles.error} role="alert">{error}</p>
          <button type="button" onClick={refreshSummary}>重新读取统计</button>
        </div>
      )}
      {/* 数量和命中率直接使用后端结果，只格式化百分比。 */}
      {!loading && !error && summary && (
        <div>
          <p>出手数：{summary.attempts}</p>
          <p>命中数：{summary.made}</p>
          <p>命中率：</p>
          <p className={styles.percentage}>{(summary.field_goals * 100).toFixed(1)}%</p>
        </div>
      )}
      {/* 返回 SingleShootingForm，不创建新组或修改已结束数据。 */}
      <button type="button" onClick={onBack} disabled={!onBack}>返回投篮组列表</button>
    </section>
  );
}
