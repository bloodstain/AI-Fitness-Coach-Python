# AI Fitness Coach Python API

FastAPI + PostgreSQL 后端，默认连接：

```env
DATABASE_URL=postgresql://postgres:guayang@127.0.0.1:5432/ai_fitness_coach
```

页面数据对应的主要表：

- `users`, `user_profiles`: 用户资料、目标、身体指标
- `daily_nutrition`, `meals`, `recognized_foods`, `dinner_options`: 今日营养、餐食、拍照识别、AI 晚餐建议
- `workout_plans`, `workout_plan_days`, `workout_exercises`, `exercise_library`: 训练计划、今日训练、动作库
- `activity_summary`, `activity_week`, `strength_progress`, `chart_series`: 运动数据和图表
- `ai_context`, `ai_messages`, `ai_suggestions`, `ai_reviews`: AI 私教聊天和复盘
- `home_plan_items`, `profile_menu_items`: 首页计划和个人页菜单

启动方式：

```bash
pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --host 127.0.0.1 --port 5000 --reload
```

前端主要读取 `GET /api/app-data`，也保留了分页面接口，例如 `/api/diet/today`、`/api/training/plan`、`/api/activity/summary`。

拍照识别接口：

- `POST /api/diet/recognize`
- 表单字段：`file`
- 配置 `OPENAI_API_KEY` 后会调用视觉模型识别真实图片；未配置时返回种子示例，保证前端流程可用。
