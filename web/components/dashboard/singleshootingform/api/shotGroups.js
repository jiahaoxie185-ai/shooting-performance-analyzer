// 复用现有请求方法，统一通过 /api 同源代理访问后端。
export {
  getShotGroups,
  createShotGroup,
  finishShotGroup,
  getShotGroupSummary,
} from "../../../../lib/api";
