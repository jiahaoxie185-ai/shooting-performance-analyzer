"use client";

import useShotGroups from "../hooks/useShotGroups";
import OngoingTraining from "./OngoingTraining";
import CompletedTrainingSummary from "./CompletedTrainingSummary";
import styles from "../../Dashboard.module.css";

// 页面负责展示，列表和页面切换状态由 hook 管理。
export default function SingleShootingForm({ sessionId, onBack }) {
  const {
    groups, loading, error, creating, createError, createGroup, updateGroup, refreshGroups,
    selectedGroup, openGroup, backToList,
  } = useShotGroups(sessionId);

  // 两个详情页面使用同一个返回操作，清空选择后展示列表。
  if (selectedGroup) {
    if (selectedGroup.ended_at) {
      return <CompletedTrainingSummary groupId={selectedGroup.id} onBack={backToList} />;
    }
    return (
      <OngoingTraining
        key={selectedGroup.id} groupId={selectedGroup.id}
        onBack={backToList} onFinished={updateGroup}
      />
    );
  }

  return (
    <section className={styles.card}>
      <div className={styles.header}>
        <h2>本场投篮组</h2>
        <button type="button" onClick={createGroup} disabled={!sessionId || loading || creating}>
          {creating ? "创建中…" : "创建投篮组"}
        </button>
      </div>
      {!sessionId && <p>请先选择一场训练</p>}
      {loading && <p role="status">正在读取投篮组…</p>}
      {error && (
        <div>
          <p className={styles.error} role="alert">{error}</p>
          <button type="button" onClick={refreshGroups} disabled={creating}>重新读取列表</button>
        </div>
      )}
      {createError && <p className={styles.error} role="alert">{createError}</p>}
      {sessionId && !loading && !error && groups.length === 0 && <p>还没有投篮组</p>}
      {!loading && !error && (
        <ul className={styles.sessions}>
          {groups.map((group) => (
            <li key={group.id}>
              <button type="button" onClick={() => openGroup(group)} disabled={creating}>
                <span>{group.started_at.replace("T", " ")}</span>
                <span>{group.ended_at ? "已结束 · 查看统计" : "进行中 · 继续填写"} →</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {/* 返回用户的场次列表，与组详情的返回操作分开。 */}
      {onBack && (
        <button type="button" onClick={onBack} disabled={creating}>返回训练场次列表</button>
      )}
    </section>
  );
}
