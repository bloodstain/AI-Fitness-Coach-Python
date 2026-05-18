CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  phone VARCHAR(32) UNIQUE,
  email VARCHAR(255) UNIQUE,
  display_name VARCHAR(80) NOT NULL,
  avatar_initials VARCHAR(12) NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  gender VARCHAR(20) NOT NULL,
  age INTEGER NOT NULL,
  height_cm INTEGER NOT NULL,
  current_weight_kg NUMERIC(5, 2) NOT NULL,
  target_weight_kg NUMERIC(5, 2) NOT NULL,
  body_fat_percent NUMERIC(5, 2) NOT NULL,
  bmi NUMERIC(5, 2) NOT NULL,
  goal VARCHAR(40) NOT NULL,
  target_date DATE,
  target_date_label VARCHAR(40) NOT NULL,
  weekly_training_days INTEGER NOT NULL,
  training_experience VARCHAR(40) NOT NULL,
  diet_preferences JSONB NOT NULL DEFAULT '[]',
  health_limitations JSONB NOT NULL DEFAULT '[]',
  membership_status VARCHAR(80) NOT NULL DEFAULT '',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS body_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  weight_kg NUMERIC(5, 2) NOT NULL,
  body_fat_percent NUMERIC(5, 2) NOT NULL,
  bmi NUMERIC(5, 2) NOT NULL,
  waist_cm NUMERIC(5, 2),
  hip_cm NUMERIC(5, 2),
  note TEXT
);

CREATE INDEX IF NOT EXISTS idx_body_metrics_user_measured ON body_metrics (user_id, measured_at DESC);

CREATE TABLE IF NOT EXISTS daily_nutrition (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  nutrition_date DATE NOT NULL,
  target_calories INTEGER NOT NULL,
  intake_calories INTEGER NOT NULL,
  remaining_calories INTEGER NOT NULL,
  burned_calories INTEGER NOT NULL,
  protein_g INTEGER NOT NULL,
  protein_target_g INTEGER NOT NULL,
  carbs_g INTEGER NOT NULL,
  carbs_target_g INTEGER NOT NULL,
  fat_g INTEGER NOT NULL,
  fat_target_g INTEGER NOT NULL,
  protein_gap_g INTEGER NOT NULL,
  UNIQUE (user_id, nutrition_date)
);

CREATE TABLE IF NOT EXISTS meals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  meal_date DATE NOT NULL,
  meal_type VARCHAR(30) NOT NULL,
  title VARCHAR(80) NOT NULL,
  subtitle VARCHAR(120) NOT NULL,
  suggested_range VARCHAR(60) NOT NULL,
  calories INTEGER NOT NULL,
  protein_g INTEGER NOT NULL,
  status VARCHAR(40) NOT NULL,
  image_key VARCHAR(40) NOT NULL,
  sort_order INTEGER NOT NULL,
  UNIQUE (user_id, meal_date, meal_type)
);

CREATE TABLE IF NOT EXISTS recognized_foods (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(80) NOT NULL,
  amount NUMERIC(8, 2) NOT NULL,
  unit VARCHAR(20) NOT NULL,
  calories INTEGER NOT NULL,
  protein_g INTEGER NOT NULL,
  carbs_g INTEGER NOT NULL,
  fat_g INTEGER NOT NULL,
  thumb_key VARCHAR(40) NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dinner_options (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  option_label VARCHAR(20) NOT NULL,
  name VARCHAR(80) NOT NULL,
  calories INTEGER NOT NULL,
  protein_g INTEGER NOT NULL,
  carbs_g INTEGER NOT NULL,
  fat_g INTEGER NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS workout_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  goal VARCHAR(40) NOT NULL,
  weekly_frequency INTEGER NOT NULL,
  location VARCHAR(40) NOT NULL,
  duration_minutes INTEGER NOT NULL,
  equipment JSONB NOT NULL DEFAULT '[]',
  preferred_exercises JSONB NOT NULL DEFAULT '[]',
  limitations JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE workout_plans
ADD COLUMN IF NOT EXISTS preferred_exercises JSONB NOT NULL DEFAULT '[]';

CREATE TABLE IF NOT EXISTS workout_plan_days (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  plan_id UUID NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
  weekday_label VARCHAR(20) NOT NULL,
  title VARCHAR(80) NOT NULL,
  duration_minutes INTEGER NOT NULL,
  focus VARCHAR(120) NOT NULL,
  icon_key VARCHAR(40) NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS workout_exercises (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  plan_day_id UUID NOT NULL REFERENCES workout_plan_days(id) ON DELETE CASCADE,
  name VARCHAR(80) NOT NULL,
  sets INTEGER NOT NULL,
  reps VARCHAR(40) NOT NULL,
  weight VARCHAR(40),
  status VARCHAR(20) NOT NULL,
  thumb_key VARCHAR(40) NOT NULL,
  rest_seconds INTEGER NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS exercise_library (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(80) NOT NULL,
  body_part VARCHAR(40) NOT NULL,
  level VARCHAR(40) NOT NULL,
  common_mistake VARCHAR(120) NOT NULL,
  target_muscle VARCHAR(80) NOT NULL,
  alternative VARCHAR(80) NOT NULL,
  image_key VARCHAR(40) NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS home_plan_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  icon_key VARCHAR(30) NOT NULL,
  title VARCHAR(80) NOT NULL,
  subtitle VARCHAR(80) NOT NULL,
  status VARCHAR(30) NOT NULL,
  value_text VARCHAR(80) NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_summary (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  weekly_workouts_done INTEGER NOT NULL,
  weekly_workouts_target INTEGER NOT NULL,
  workout_minutes INTEGER NOT NULL,
  calories_burned INTEGER NOT NULL,
  steps INTEGER NOT NULL,
  avg_heart_rate INTEGER NOT NULL,
  max_heart_rate INTEGER NOT NULL,
  training_load_total INTEGER NOT NULL,
  synced_device VARCHAR(80) NOT NULL,
  synced_status VARCHAR(40) NOT NULL,
  synced_ago VARCHAR(40) NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_week (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  weekday_label VARCHAR(20) NOT NULL,
  day_label VARCHAR(20) NOT NULL,
  done BOOLEAN NOT NULL,
  active BOOLEAN NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS strength_progress (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(80) NOT NULL,
  value_text VARCHAR(40) NOT NULL,
  delta_text VARCHAR(40) NOT NULL,
  image_key VARCHAR(40) NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS chart_series (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  heart_rate_samples JSONB NOT NULL,
  training_load_samples JSONB NOT NULL,
  review_weight_samples JSONB NOT NULL,
  review_train_samples JSONB NOT NULL,
  review_diet_samples JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_context (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  goal_label VARCHAR(80) NOT NULL,
  calories_label VARCHAR(80) NOT NULL,
  workouts_label VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL,
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  created_time VARCHAR(20) NOT NULL,
  bullets JSONB NOT NULL DEFAULT '[]',
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_suggestions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  icon_key VARCHAR(40) NOT NULL,
  text VARCHAR(120) NOT NULL,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_reviews (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  review_date DATE NOT NULL,
  score INTEGER NOT NULL,
  score_label VARCHAR(40) NOT NULL,
  diet_percent INTEGER NOT NULL,
  training_label VARCHAR(40) NOT NULL,
  water_current_ml INTEGER NOT NULL,
  water_target_ml INTEGER NOT NULL,
  good_tip TEXT NOT NULL,
  adjust_tip TEXT NOT NULL,
  weight_delta_kg NUMERIC(5, 2) NOT NULL,
  training_completion_percent INTEGER NOT NULL,
  diet_completion_percent INTEGER NOT NULL,
  UNIQUE (user_id, review_date)
);

CREATE TABLE IF NOT EXISTS profile_menu_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  icon_key VARCHAR(40) NOT NULL,
  title VARCHAR(80) NOT NULL,
  note VARCHAR(120) NOT NULL,
  sort_order INTEGER NOT NULL
);
