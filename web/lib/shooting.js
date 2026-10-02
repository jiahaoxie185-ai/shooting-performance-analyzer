export const SHOOTING_ZONES = [
  ["paint", "篮下"],
  ["left_midrange", "左侧中距离"],
  ["right_midrange", "右侧中距离"],
  ["top_midrange", "弧顶中距离"],
  ["left_corner", "左侧底角三分"],
  ["right_corner", "右侧底角三分"],
  ["top_three", "弧顶三分"],
];

export function summarizeShots(shots) {
  const attempts = shots.length;
  const made = shots.filter((shot) => shot.made === true).length;
  return { attempts, made, percentage: attempts ? made / attempts * 100 : 0 };
}

// 按浏览器本地日期筛选逐球记录，再计算比例，不平均各场命中率。
export function summarizeToday(sessions, now = new Date()) {
  const shots = sessions.flatMap((session) => session.shots).filter((shot) => {
    const date = new Date(shot.attempted_at);
    return date.getFullYear() === now.getFullYear()
      && date.getMonth() === now.getMonth()
      && date.getDate() === now.getDate();
  });
  return summarizeShots(shots);
}
