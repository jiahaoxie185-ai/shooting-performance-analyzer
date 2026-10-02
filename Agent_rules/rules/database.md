# 数据库使用约束

## 存储与模型

- 沿用 SQLite 和 SQLAlchemy；数据库路径由 `infrastructure/database.py` 根据仓库位置确定，为根目录 `basketball.db`。
- ORM 表定义集中在 `infrastructure/models.py`，数据库访问集中在 `infrastructure/repositories/`。
- 领域实体与 ORM 模型分离，由仓储负责转换。
- 当前四张表：`users`、`shooting_sessions`、`shot_attempts`、`auth_session`。不要混淆训练场次与认证会话。

## 数据关系与约束

- `users.id` 为用户主键，`username` 唯一且非空，密码仅保存哈希。
- `shooting_sessions.user_id` 外键引用 `users.id`。
- `shot_attempts.session_id` 外键引用 `shooting_sessions.id`；区域使用现有枚举字符串，命中结果使用布尔值。
- `auth_session.token_hash` 为主键；`user_id` 引用用户，`expires_at` 保存 Unix 秒级时间戳。
- 每个数据库连接启用 SQLite 外键检查；新增引擎时不能遗漏该配置。
- 当前外键未声明级联删除；新增删除功能前明确关联数据的保留或删除规则，不假设会自动级联。
- 当前训练时间字段使用 DateTime，认证过期时间使用 Unix 秒；变更时间表示或时区策略需同步读写逻辑并明确迁移方案。

## 事务与查询

- 用户、训练和认证会话仓储共用工作单元创建的 Session。
- 仓储只查询、添加、更新或删除；提交、回滚和关闭由工作单元负责。
- 保存训练信息与新增投篮分别使用 `save_session()` 和 `add_shot()`；训练外键目标必须存在于当前事务中。
- 使用 SQLAlchemy 条件构造查询，不拼接用户输入生成 SQL。
- 查询结果保持确定顺序。现有投篮查询按时间和 ID 排序，训练列表沿用仓储中的排序规则。
- 无资源返回约定的 `None` 或空列表，由服务层决定业务处理，不伪造占位数据。
- 不单独持久化可从投篮记录计算的命中率，避免投篮记录与统计结果失步。

## 初始化与结构变更

- `python -m infrastructure.init_db` 使用 `Base.metadata.create_all()` 创建不存在的表；此操作会写入数据库。
- `create_all()` 不迁移已有表结构。改字段、约束或表结构前必须制定明确的数据迁移方案。
- 不通过删除数据库、重建数据库或清空用户数据来代替迁移；涉及数据删除应取得明确授权。
- `basketball.db` 和数据库辅助文件保持本地存储，不纳入 Git；现有根目录 `.gitignore` 已配置相关忽略项。
- 不在文档、日志或仓库中暴露密码、原始令牌或用户数据。

## 证据路径

`infrastructure/database.py`、`infrastructure/models.py`、`infrastructure/init_db.py`、`infrastructure/unit_of_work.py`、`infrastructure/repositories/`、`.gitignore`。
