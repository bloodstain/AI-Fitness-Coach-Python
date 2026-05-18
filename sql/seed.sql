INSERT INTO users (id, phone, display_name, avatar_initials)
VALUES ('00000000-0000-0000-0000-000000000001', '13800000000', '林晨', 'LC')
ON CONFLICT (id) DO UPDATE SET display_name = EXCLUDED.display_name, avatar_initials = EXCLUDED.avatar_initials;

INSERT INTO user_profiles (
  user_id, gender, age, height_cm, current_weight_kg, target_weight_kg,
  body_fat_percent, bmi, goal, target_date, target_date_label,
  weekly_training_days, training_experience, diet_preferences,
  health_limitations, membership_status
)
VALUES (
  '00000000-0000-0000-0000-000000000001', 'male', 28, 175, 72.4, 68,
  21.8, 23.1, '减脂', '2026-08-30', '8月30日',
  4, '有基础', '["高蛋白", "少油", "不吃辣"]',
  '["膝盖无伤", "腰背正常"]', 'Pro 试用中'
)
ON CONFLICT (user_id) DO UPDATE SET
  current_weight_kg = EXCLUDED.current_weight_kg,
  target_weight_kg = EXCLUDED.target_weight_kg,
  body_fat_percent = EXCLUDED.body_fat_percent,
  bmi = EXCLUDED.bmi,
  goal = EXCLUDED.goal,
  weekly_training_days = EXCLUDED.weekly_training_days,
  updated_at = NOW();

INSERT INTO body_metrics (user_id, measured_at, weight_kg, body_fat_percent, bmi, waist_cm, hip_cm, note)
SELECT '00000000-0000-0000-0000-000000000001', NOW(), 72.4, 21.8, 23.1, 82, 96, '初始身体数据'
WHERE NOT EXISTS (
  SELECT 1 FROM body_metrics WHERE user_id = '00000000-0000-0000-0000-000000000001'
);

INSERT INTO daily_nutrition (
  user_id, nutrition_date, target_calories, intake_calories, remaining_calories,
  burned_calories, protein_g, protein_target_g, carbs_g, carbs_target_g,
  fat_g, fat_target_g, protein_gap_g
)
VALUES (
  '00000000-0000-0000-0000-000000000001', CURRENT_DATE, 1800, 1260, 540,
  420, 82, 120, 138, 200, 42, 60, 38
)
ON CONFLICT (user_id, nutrition_date) DO UPDATE SET
  intake_calories = EXCLUDED.intake_calories,
  remaining_calories = EXCLUDED.remaining_calories,
  burned_calories = EXCLUDED.burned_calories,
  protein_g = EXCLUDED.protein_g,
  carbs_g = EXCLUDED.carbs_g,
  fat_g = EXCLUDED.fat_g;

DELETE FROM meals WHERE user_id = '00000000-0000-0000-0000-000000000001';
INSERT INTO meals (user_id, meal_date, meal_type, title, subtitle, suggested_range, calories, protein_g, status, image_key, sort_order)
VALUES
  ('00000000-0000-0000-0000-000000000001', CURRENT_DATE, 'breakfast', '早餐', '燕麦牛奶', '建议 450-550 kcal', 320, 18, '已记录', 'oatmeal', 1),
  ('00000000-0000-0000-0000-000000000001', CURRENT_DATE, 'lunch', '午餐', '鸡胸肉饭', '建议 600-700 kcal', 491, 46, '已记录', 'chicken', 2),
  ('00000000-0000-0000-0000-000000000001', CURRENT_DATE, 'dinner', '晚餐', '拍照记录晚餐', '建议 450-550 kcal', 0, 0, '待记录', 'dish', 3),
  ('00000000-0000-0000-0000-000000000001', CURRENT_DATE, 'snack', '加餐', '记录加餐', '建议 150-250 kcal', 449, 0, '可添加', 'snack', 4);

DELETE FROM recognized_foods WHERE user_id = '00000000-0000-0000-0000-000000000001';
INSERT INTO recognized_foods (user_id, name, amount, unit, calories, protein_g, carbs_g, fat_g, thumb_key, sort_order)
VALUES
  ('00000000-0000-0000-0000-000000000001', '鸡胸肉', 150, 'g', 248, 34, 1, 5, 'chicken', 1),
  ('00000000-0000-0000-0000-000000000001', '米饭', 120, 'g', 139, 3, 31, 0, 'rice', 2),
  ('00000000-0000-0000-0000-000000000001', '西兰花', 100, 'g', 34, 3, 7, 0, 'broccoli', 3),
  ('00000000-0000-0000-0000-000000000001', '鸡蛋', 1, '个', 70, 6, 1, 5, 'egg', 4);

DELETE FROM dinner_options WHERE user_id = '00000000-0000-0000-0000-000000000001';
INSERT INTO dinner_options (user_id, option_label, name, calories, protein_g, carbs_g, fat_g, sort_order)
VALUES
  ('00000000-0000-0000-0000-000000000001', '方案A', '鸡胸肉沙拉', 430, 42, 22, 12, 1),
  ('00000000-0000-0000-0000-000000000001', '方案B', '虾仁豆腐饭', 510, 39, 55, 14, 2),
  ('00000000-0000-0000-0000-000000000001', '方案C', '牛肉蔬菜汤', 460, 36, 28, 18, 3);

INSERT INTO workout_plans (id, user_id, goal, weekly_frequency, location, duration_minutes, equipment, preferred_exercises, limitations)
VALUES (
  '00000000-0000-0000-0000-000000000101',
  '00000000-0000-0000-0000-000000000001',
  '减脂', 4, '健身房', 45, '["哑铃", "杠铃", "跑步机"]', '[]', '["膝盖无伤", "腰背正常"]'
)
ON CONFLICT (id) DO UPDATE SET
  goal = EXCLUDED.goal,
  weekly_frequency = EXCLUDED.weekly_frequency,
  location = EXCLUDED.location,
  duration_minutes = EXCLUDED.duration_minutes,
  equipment = EXCLUDED.equipment,
  limitations = EXCLUDED.limitations;

INSERT INTO workout_plan_days (id, plan_id, weekday_label, title, duration_minutes, focus, icon_key, sort_order)
VALUES
  ('00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000101', '周一', '上肢力量', 45, '重点胸背肌', 'muscle', 1),
  ('00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000101', '周二', '有氧', 45, '中等强度有氧', 'run', 2),
  ('00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000101', '周四', '下肢力量', 45, '重点腿臀', 'leg', 3),
  ('00000000-0000-0000-0000-000000000204', '00000000-0000-0000-0000-000000000101', '周六', '全身循环', 45, '全身综合训练', 'cycle', 4)
ON CONFLICT (id) DO UPDATE SET
  weekday_label = EXCLUDED.weekday_label,
  title = EXCLUDED.title,
  duration_minutes = EXCLUDED.duration_minutes,
  focus = EXCLUDED.focus,
  icon_key = EXCLUDED.icon_key,
  sort_order = EXCLUDED.sort_order;

INSERT INTO workout_exercises (plan_day_id, name, sets, reps, weight, status, thumb_key, rest_seconds, sort_order)
SELECT * FROM (
  VALUES
    ('00000000-0000-0000-0000-000000000201'::uuid, '哑铃卧推', 4, '10次', '20kg', 'done', 'bench', 75, 1),
    ('00000000-0000-0000-0000-000000000201'::uuid, '坐姿划船', 4, '12次', '35kg', 'active', 'row', 75, 2),
    ('00000000-0000-0000-0000-000000000201'::uuid, '肩推', 3, '10次', '15kg', 'todo', 'press', 60, 3),
    ('00000000-0000-0000-0000-000000000201'::uuid, '平板支撑', 3, '45秒', '自重', 'todo', 'plank', 45, 4)
) AS seed(plan_day_id, name, sets, reps, weight, status, thumb_key, rest_seconds, sort_order)
WHERE NOT EXISTS (
  SELECT 1 FROM workout_exercises WHERE plan_day_id = '00000000-0000-0000-0000-000000000201'
);

DELETE FROM exercise_library;
INSERT INTO exercise_library (name, body_part, level, common_mistake, target_muscle, alternative, image_key, sort_order)
VALUES
  ('深蹲', '腿部', '中级', '膝盖内扣', '股四头肌', '箱式深蹲', 'squat', 1),
  ('卧推', '胸部', '中级', '肩胛不稳定', '胸大肌', '哑铃卧推', 'bench', 2),
  ('硬拉', '背腿', '高级', '弓背发力', '腘绳肌', '壶铃硬拉', 'deadlift', 3),
  ('平板支撑', '核心', '新手', '塌腰', '腹横肌', '死虫', 'plank', 4);

DELETE FROM home_plan_items;
INSERT INTO home_plan_items (icon_key, title, subtitle, status, value_text, sort_order)
VALUES
  ('meal', '早餐', '已完成', 'done', '', 1),
  ('meal', '午餐', '待确认', 'pending', '', 2),
  ('workout', '18:30 力量训练', '下次训练', 'next', '', 3),
  ('water', '2200ml 饮水目标', '已喝 1200ml', 'progress', '1200/2200ml', 4);

INSERT INTO activity_summary (
  user_id, weekly_workouts_done, weekly_workouts_target, workout_minutes,
  calories_burned, steps, avg_heart_rate, max_heart_rate, training_load_total,
  synced_device, synced_status, synced_ago
)
VALUES (
  '00000000-0000-0000-0000-000000000001', 3, 4, 156, 1280, 7420,
  128, 168, 2560, 'Apple Health', '已同步', '5分钟前'
)
ON CONFLICT (user_id) DO UPDATE SET
  weekly_workouts_done = EXCLUDED.weekly_workouts_done,
  workout_minutes = EXCLUDED.workout_minutes,
  calories_burned = EXCLUDED.calories_burned,
  steps = EXCLUDED.steps;

DELETE FROM activity_week;
INSERT INTO activity_week (weekday_label, day_label, done, active, sort_order)
VALUES
  ('周一', '6/2', true, false, 1),
  ('周二', '6/3', true, false, 2),
  ('周三', '6/4', true, false, 3),
  ('周四', '6/5', false, true, 4),
  ('周五', '6/6', false, false, 5),
  ('周六', '6/7', false, false, 6),
  ('周日', '6/8', false, false, 7);

DELETE FROM strength_progress;
INSERT INTO strength_progress (name, value_text, delta_text, image_key, sort_order)
VALUES
  ('卧推', '42.5 kg', '+2.5 kg', 'bench', 1),
  ('深蹲', '60 kg', '+5 kg', 'squat', 2);

DELETE FROM chart_series;
INSERT INTO chart_series (
  heart_rate_samples, training_load_samples, review_weight_samples,
  review_train_samples, review_diet_samples
)
VALUES (
  '[86,88,92,99,105,112,118,121,119,127,123,134,138,136,141,137,146,155,132,139,147,152,160,168,151,142,128,122,119,108,112]',
  '[560,680,720,600,360,300,300]',
  '[72.8,72.6,72.55,72.35,72.4,72.05,71.88,71.64]',
  '[56,68,76,94,58,72]',
  '[54,66,60,78,76,61]'
);

INSERT INTO ai_context (user_id, goal_label, calories_label, workouts_label)
VALUES ('00000000-0000-0000-0000-000000000001', '减脂目标', '今日 1260kcal', '本周 3 练')
ON CONFLICT (user_id) DO UPDATE SET
  goal_label = EXCLUDED.goal_label,
  calories_label = EXCLUDED.calories_label,
  workouts_label = EXCLUDED.workouts_label;

DELETE FROM ai_messages WHERE conversation_id = '00000000-0000-0000-0000-000000000401';
INSERT INTO ai_messages (conversation_id, role, content, created_time, bullets, sort_order)
VALUES
  ('00000000-0000-0000-0000-000000000401', 'user', '今天午餐吃多了，晚餐怎么补救？', '15:30', '[]', 1),
  ('00000000-0000-0000-0000-000000000401', 'assistant', '别担心，晚餐可以这样调整来帮助你控制热量，稳住目标：', '15:30',
   '["晚餐控制在 450kcal 内", "优先蛋白质 35g，增强饱腹感并帮助肌肉修复", "减少油脂和精制碳水，选择低 GI 食物", "训练后补水，建议 500-700ml"]', 2);

DELETE FROM ai_suggestions;
INSERT INTO ai_suggestions (icon_key, text, sort_order)
VALUES
  ('dumbbell', '明天练什么', 1),
  ('weight', '体重不降怎么办', 2),
  ('run', '替换动作', 3);

INSERT INTO ai_reviews (
  user_id, review_date, score, score_label, diet_percent, training_label,
  water_current_ml, water_target_ml, good_tip, adjust_tip, weight_delta_kg,
  training_completion_percent, diet_completion_percent
)
VALUES (
  '00000000-0000-0000-0000-000000000001', CURRENT_DATE, 82, '良好', 78,
  '已完成', 1900, 2200, '蛋白质摄入接近目标，力量训练按计划完成。',
  '午餐油脂偏高，晚餐保持清淡并补足蔬菜。', -0.4, 75, 68
)
ON CONFLICT (user_id, review_date) DO UPDATE SET
  score = EXCLUDED.score,
  diet_percent = EXCLUDED.diet_percent,
  training_label = EXCLUDED.training_label;

DELETE FROM profile_menu_items;
INSERT INTO profile_menu_items (icon_key, title, note, sort_order)
VALUES
  ('body', '身体数据', '', 1),
  ('target', '我的目标', '', 2),
  ('watch', '设备同步', '体脂秤 未连接', 3),
  ('vip', '会员中心', '', 4),
  ('bell', '通知设置', '', 5),
  ('lock', '隐私与数据', '', 6);
