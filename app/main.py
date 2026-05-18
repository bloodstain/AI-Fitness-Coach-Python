import json
from datetime import date, datetime

from fastapi import Body, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.db import execute, fetch_all, fetch_one, init_schema_and_seed
from app.food_recognition import recognize_food_image


DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"


app = FastAPI(title="AI Fitness Coach API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_schema_and_seed()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-fitness-coach-python"}


@app.get("/api/users/me")
def get_current_user():
    return fetch_one(
        """
        SELECT
          u.id,
          u.display_name AS name,
          u.avatar_initials AS avatar,
          p.gender,
          p.age,
          p.height_cm,
          p.current_weight_kg AS weight_kg,
          p.target_weight_kg,
          p.body_fat_percent,
          p.bmi,
          p.goal,
          p.target_date,
          p.target_date_label,
          p.weekly_training_days,
          p.training_experience,
          p.diet_preferences,
          p.health_limitations,
          p.membership_status
        FROM users u
        JOIN user_profiles p ON p.user_id = u.id
        WHERE u.id = '00000000-0000-0000-0000-000000000001'
        """
    )


def target_date_label(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return value
    return f"{parsed.month}月{parsed.day}日"


@app.patch("/api/users/me/profile")
def update_user_profile(payload: dict = Body(...)):
    gender = str(payload.get("gender") or "male")
    age = int(payload.get("age") or 0)
    height = int(payload.get("height_cm") or 0)
    current_weight = float(payload.get("weight_kg") or 0)
    target_weight = float(payload.get("target_weight_kg") or 0)
    goal = str(payload.get("goal") or "减脂")
    target_date_value = str(payload.get("target_date") or "")
    weekly_days = int(payload.get("weekly_training_days") or 4)
    training_experience = str(payload.get("training_experience") or "有基础")
    diet_preferences = payload.get("diet_preferences") or []
    health_limitations = payload.get("health_limitations") or []

    if age <= 0 or height <= 0 or current_weight <= 0 or target_weight <= 0:
        raise HTTPException(status_code=400, detail="age, height_cm, weight_kg and target_weight_kg are required")
    if weekly_days < 1 or weekly_days > 7:
        raise HTTPException(status_code=400, detail="weekly_training_days must be between 1 and 7")
    if not isinstance(diet_preferences, list):
        diet_preferences = []
    if not isinstance(health_limitations, list):
        health_limitations = []

    target_date_db: date | None = None
    if target_date_value:
        try:
            target_date_db = datetime.strptime(target_date_value[:10], "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="target_date must be YYYY-MM-DD") from exc

    profile = execute(
        """
        UPDATE user_profiles
        SET gender = %s,
            age = %s,
            height_cm = %s,
            current_weight_kg = %s,
            target_weight_kg = %s,
            goal = %s,
            target_date = %s,
            target_date_label = %s,
            weekly_training_days = %s,
            training_experience = %s,
            diet_preferences = %s::jsonb,
            health_limitations = %s::jsonb,
            updated_at = NOW()
        WHERE user_id = %s::uuid
        RETURNING gender, age, height_cm, current_weight_kg AS weight_kg,
                  target_weight_kg, body_fat_percent, bmi, goal, target_date,
                  target_date_label, weekly_training_days, training_experience,
                  diet_preferences, health_limitations, membership_status
        """,
        (
            gender,
            age,
            height,
            current_weight,
            target_weight,
            goal,
            target_date_db,
            target_date_label(target_date_value),
            weekly_days,
            training_experience,
            json.dumps(diet_preferences, ensure_ascii=False),
            json.dumps(health_limitations, ensure_ascii=False),
            DEMO_USER_ID,
        ),
    )
    if not profile:
        raise HTTPException(status_code=404, detail="profile not found")

    execute(
        """
        UPDATE activity_summary
        SET weekly_workouts_target = %s
        WHERE user_id = %s::uuid
        """,
        (weekly_days, DEMO_USER_ID),
    )
    execute(
        """
        INSERT INTO ai_context (user_id, goal_label, calories_label, workouts_label)
        VALUES (%s::uuid, %s, '今日 1260kcal', %s)
        ON CONFLICT (user_id) DO UPDATE SET
          goal_label = EXCLUDED.goal_label,
          workouts_label = EXCLUDED.workouts_label
        """,
        (DEMO_USER_ID, f"{goal}目标", f"本周 {weekly_days} 练"),
    )
    user = get_current_user()
    return user


@app.get("/api/users/me/body-metrics")
def get_body_metrics():
    latest = fetch_one(
        """
        SELECT id, measured_at, weight_kg, body_fat_percent, bmi, waist_cm, hip_cm, note
        FROM body_metrics
        WHERE user_id = %s::uuid
        ORDER BY measured_at DESC
        LIMIT 1
        """,
        (DEMO_USER_ID,),
    )
    history = fetch_all(
        """
        SELECT id, measured_at, weight_kg, body_fat_percent, bmi, waist_cm, hip_cm, note
        FROM body_metrics
        WHERE user_id = %s::uuid
        ORDER BY measured_at DESC
        LIMIT 10
        """,
        (DEMO_USER_ID,),
    )
    return {"latest": latest, "history": history}


@app.post("/api/users/me/body-metrics")
def save_body_metrics(payload: dict = Body(...)):
    weight = float(payload.get("weight_kg") or 0)
    body_fat = float(payload.get("body_fat_percent") or 0)
    bmi = float(payload.get("bmi") or 0)
    waist = payload.get("waist_cm")
    hip = payload.get("hip_cm")
    note = str(payload.get("note") or "")
    if weight <= 0 or body_fat <= 0 or bmi <= 0:
        raise HTTPException(status_code=400, detail="weight_kg, body_fat_percent and bmi are required")

    metric = execute(
        """
        INSERT INTO body_metrics (user_id, weight_kg, body_fat_percent, bmi, waist_cm, hip_cm, note)
        VALUES (%s::uuid, %s, %s, %s, %s, %s, %s)
        RETURNING id, measured_at, weight_kg, body_fat_percent, bmi, waist_cm, hip_cm, note
        """,
        (DEMO_USER_ID, weight, body_fat, bmi, waist, hip, note),
    )
    execute(
        """
        UPDATE user_profiles
        SET current_weight_kg = %s,
            body_fat_percent = %s,
            bmi = %s,
            updated_at = NOW()
        WHERE user_id = %s::uuid
        """,
        (weight, body_fat, bmi, DEMO_USER_ID),
    )
    return metric


@app.get("/api/diet/today")
def get_today_diet():
    nutrition = fetch_one(
        """
        SELECT target_calories, intake_calories, remaining_calories, burned_calories,
               protein_g, protein_target_g, carbs_g, carbs_target_g, fat_g, fat_target_g,
               protein_gap_g
        FROM daily_nutrition
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
        ORDER BY nutrition_date DESC
        LIMIT 1
        """
    )
    meals = fetch_all(
        """
        SELECT meal_type, title, subtitle, suggested_range, calories, protein_g, status, image_key
        FROM meals
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
        ORDER BY sort_order
        """
    )
    recognized_foods = fetch_all(
        """
        SELECT name, amount, unit, calories, protein_g, carbs_g, fat_g, thumb_key
        FROM recognized_foods
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
        ORDER BY sort_order
        """
    )
    dinner_options = fetch_all(
        """
        SELECT option_label, name, calories, protein_g, carbs_g, fat_g
        FROM dinner_options
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
        ORDER BY sort_order
        """
    )
    return {
        "nutrition": nutrition,
        "meals": meals,
        "recognizedFoods": recognized_foods,
        "dinnerOptions": dinner_options,
    }


@app.post("/api/diet/recognize")
async def recognize_meal(file: UploadFile | None = None):
    if file is not None:
        image_bytes = await file.read()
        if image_bytes:
            result = recognize_food_image(
                image_bytes,
                file.content_type or "image/jpeg",
            )
            if result is not None:
                return result

    foods = fetch_all(
        """
        SELECT name, amount, unit, calories, protein_g, carbs_g, fat_g, thumb_key
        FROM recognized_foods
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
        ORDER BY sort_order
        """
    )
    return {
        "confidence": 0.86,
        "total_calories": sum(item["calories"] for item in foods),
        "items": foods,
        "source": "seed",
    }


@app.get("/api/diet/advice")
def get_diet_advice():
    return {
        "remaining_calories": 540,
        "protein_gap_g": 38,
        "options": fetch_all(
            """
            SELECT option_label, name, calories, protein_g, carbs_g, fat_g
            FROM dinner_options
            WHERE user_id = '00000000-0000-0000-0000-000000000001'
            ORDER BY sort_order
            """
        ),
    }


@app.get("/api/training/plan")
def get_training_plan():
    plan = fetch_one(
        """
        SELECT id, goal, weekly_frequency, location, duration_minutes, equipment, preferred_exercises, limitations
        FROM workout_plans
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="workout plan not found")
    days = fetch_all(
        """
        SELECT weekday_label, title, duration_minutes, focus, icon_key
        FROM workout_plan_days
        WHERE plan_id = %s::uuid
        ORDER BY sort_order
        """,
        (plan["id"],),
    )
    return {**plan, "weekPlan": days}


def build_plan_days(goal: str, frequency: int, duration: int) -> list[dict[str, str | int]]:
    templates = {
        "减脂": [
            ("周一", "上肢力量", "重点胸背肌", "muscle"),
            ("周二", "有氧", "中等强度有氧", "run"),
            ("周四", "下肢力量", "重点腿臀", "leg"),
            ("周六", "全身循环", "全身综合训练", "cycle"),
            ("周日", "低强度有氧", "快走或椭圆机", "run"),
            ("周三", "核心训练", "核心稳定与拉伸", "cycle"),
        ],
        "增肌": [
            ("周一", "胸肩三头", "卧推与推举", "muscle"),
            ("周二", "背部二头", "划船与下拉", "muscle"),
            ("周四", "腿臀力量", "深蹲硬拉", "leg"),
            ("周六", "上肢强化", "弱项补强", "muscle"),
            ("周日", "核心恢复", "腹部与灵活性", "cycle"),
            ("周三", "泵感训练", "中等重量容量", "muscle"),
        ],
        "塑形": [
            ("周一", "全身塑形", "复合动作循环", "cycle"),
            ("周二", "臀腿训练", "臀腿线条", "leg"),
            ("周四", "上肢线条", "肩背手臂", "muscle"),
            ("周六", "核心有氧", "核心与燃脂", "run"),
            ("周日", "拉伸恢复", "灵活性训练", "cycle"),
            ("周三", "轻力量", "动作质量", "muscle"),
        ],
        "体能": [
            ("周一", "间歇有氧", "心肺间歇", "run"),
            ("周二", "全身力量", "基础力量", "cycle"),
            ("周四", "速度耐力", "跑步机节奏", "run"),
            ("周六", "循环训练", "综合体能", "cycle"),
            ("周日", "恢复训练", "低强度活动", "run"),
            ("周三", "核心稳定", "抗旋与平衡", "cycle"),
        ],
    }
    selected = templates.get(goal, templates["减脂"])[: max(3, min(6, frequency))]
    return [
        {
            "weekday_label": weekday,
            "title": title,
            "duration_minutes": duration,
            "focus": focus,
            "icon_key": icon,
            "sort_order": index,
        }
        for index, (weekday, title, focus, icon) in enumerate(selected, start=1)
    ]


@app.post("/api/training/plan/generate")
def generate_training_plan(payload: dict = Body(...)):
    goal = str(payload.get("goal") or "减脂")
    frequency = int(payload.get("weekly_frequency") or 4)
    duration = int(payload.get("duration_minutes") or 45)
    location = str(payload.get("location") or "健身房")
    equipment = payload.get("equipment") or []
    preferred_exercises = payload.get("preferred_exercises") or []
    limitations = payload.get("limitations") or []
    days = build_plan_days(goal, frequency, duration)

    plan = execute(
        """
        INSERT INTO workout_plans (user_id, goal, weekly_frequency, location, duration_minutes, equipment, preferred_exercises, limitations)
        VALUES (%s::uuid, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
        RETURNING id, goal, weekly_frequency, location, duration_minutes, equipment, preferred_exercises, limitations
        """,
        (
            DEMO_USER_ID,
            goal,
            frequency,
            location,
            duration,
            json.dumps(equipment),
            json.dumps(preferred_exercises),
            json.dumps(limitations),
        ),
    )
    if plan is None:
        raise HTTPException(status_code=500, detail="failed to create workout plan")

    for day in days:
        execute(
            """
            INSERT INTO workout_plan_days (plan_id, weekday_label, title, duration_minutes, focus, icon_key, sort_order)
            VALUES (%s::uuid, %s, %s, %s, %s, %s, %s)
            """,
            (
                plan["id"],
                day["weekday_label"],
                day["title"],
                day["duration_minutes"],
                day["focus"],
                day["icon_key"],
                day["sort_order"],
            ),
        )

    saved_days = fetch_all(
        """
        SELECT weekday_label, title, duration_minutes, focus, icon_key
        FROM workout_plan_days
        WHERE plan_id = %s::uuid
        ORDER BY sort_order
        """,
        (plan["id"],),
    )
    return {**plan, "weekPlan": saved_days}


@app.get("/api/training/plans")
def get_training_plan_history():
    return fetch_all(
        """
        SELECT id, goal, weekly_frequency, location, duration_minutes, equipment,
               preferred_exercises, limitations, created_at
        FROM workout_plans
        WHERE user_id = %s::uuid
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (DEMO_USER_ID,),
    )


@app.get("/api/training/plans/{plan_id}")
def get_training_plan_by_id(plan_id: str):
    plan = fetch_one(
        """
        SELECT id, goal, weekly_frequency, location, duration_minutes, equipment,
               preferred_exercises, limitations, created_at
        FROM workout_plans
        WHERE id = %s::uuid AND user_id = %s::uuid
        """,
        (plan_id, DEMO_USER_ID),
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="workout plan not found")
    days = fetch_all(
        """
        SELECT weekday_label, title, duration_minutes, focus, icon_key
        FROM workout_plan_days
        WHERE plan_id = %s::uuid
        ORDER BY sort_order
        """,
        (plan_id,),
    )
    return {**plan, "weekPlan": days}


@app.get("/api/training/today")
def get_today_workout():
    exercises = fetch_all(
        """
        SELECT id, name, sets, reps, weight, status, thumb_key, rest_seconds, sort_order
        FROM workout_exercises
        WHERE plan_day_id = '00000000-0000-0000-0000-000000000201'
        ORDER BY sort_order
        """
    )
    return {
        "title": "上肢力量",
        "duration_minutes": 45,
        "completed_exercises": 3,
        "total_exercises": 7,
        "timer": "18:24",
        "exercises": exercises,
    }


@app.get("/api/training/exercises")
def get_exercise_library():
    return fetch_all(
        """
        SELECT id, name, body_part, level, common_mistake, target_muscle, alternative, image_key
        FROM exercise_library
        ORDER BY sort_order
        """
    )


def replace_today_workout_exercise_record(
    workout_exercise_id: str,
    payload: dict[str, str],
):
    library_exercise_id = payload.get("exercise_id")
    if not library_exercise_id:
        raise HTTPException(status_code=400, detail="exercise_id is required")

    updated = execute(
        """
        UPDATE workout_exercises AS we
        SET
          name = el.name,
          thumb_key = el.image_key,
          weight = CASE
            WHEN el.name = '硬拉' THEN '40kg'
            WHEN el.name = '深蹲' THEN '60kg'
            WHEN el.name = '卧推' THEN '20kg'
            WHEN el.name = '平板支撑' THEN '自重'
            ELSE we.weight
          END,
          reps = CASE
            WHEN el.name = '平板支撑' THEN '45秒'
            ELSE we.reps
          END
        FROM exercise_library AS el
        WHERE we.id = %s::uuid
          AND el.id = %s::uuid
        RETURNING we.id, we.name, we.sets, we.reps, we.weight, we.status, we.thumb_key, we.rest_seconds, we.sort_order
        """,
        (workout_exercise_id, library_exercise_id),
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="workout exercise or library exercise not found")
    return updated


@app.patch("/api/training/today/exercises/{workout_exercise_id}/replace")
def replace_today_workout_exercise(
    workout_exercise_id: str,
    payload: dict[str, str] = Body(...),
):
    return replace_today_workout_exercise_record(workout_exercise_id, payload)


@app.post("/api/training/today/exercises/{workout_exercise_id}/replace")
def post_replace_today_workout_exercise(
    workout_exercise_id: str,
    payload: dict[str, str] = Body(...),
):
    return replace_today_workout_exercise_record(workout_exercise_id, payload)


@app.get("/api/activity/summary")
def get_activity_summary():
    summary = fetch_one(
        """
        SELECT weekly_workouts_done, weekly_workouts_target, workout_minutes,
               calories_burned, steps, avg_heart_rate, max_heart_rate,
               training_load_total, synced_device, synced_status, synced_ago
        FROM activity_summary
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
        """
    )
    week = fetch_all("SELECT weekday_label, day_label, done, active FROM activity_week ORDER BY sort_order")
    strength = fetch_all("SELECT name, value_text, delta_text, image_key FROM strength_progress ORDER BY sort_order")
    charts = fetch_one("SELECT heart_rate_samples, training_load_samples FROM chart_series LIMIT 1")
    return {**summary, "week": week, "strength": strength, "charts": charts}


@app.get("/api/ai/chat")
def get_ai_chat():
    return {
        "context": fetch_one(
            """
            SELECT goal_label, calories_label, workouts_label
            FROM ai_context
            WHERE user_id = '00000000-0000-0000-0000-000000000001'
            """
        ),
        "messages": fetch_all(
            """
            SELECT role, content, created_time, bullets
            FROM ai_messages
            WHERE conversation_id = '00000000-0000-0000-0000-000000000401'
            ORDER BY sort_order
            """
        ),
        "suggestions": fetch_all("SELECT icon_key, text FROM ai_suggestions ORDER BY sort_order"),
    }


@app.get("/api/ai/review")
def get_ai_review():
    review = fetch_one(
        """
        SELECT score, score_label, diet_percent, training_label, water_current_ml,
               water_target_ml, good_tip, adjust_tip, weight_delta_kg,
               training_completion_percent, diet_completion_percent
        FROM ai_reviews
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
        ORDER BY review_date DESC
        LIMIT 1
        """
    )
    charts = fetch_one(
        """
        SELECT review_weight_samples, review_train_samples, review_diet_samples
        FROM chart_series
        LIMIT 1
        """
    )
    return {**review, "charts": charts}


@app.get("/api/app-data")
def get_app_data():
    return {
        "user": get_current_user(),
        "diet": get_today_diet(),
        "training": get_training_plan(),
        "todayWorkout": get_today_workout(),
        "exerciseLibrary": get_exercise_library(),
        "activity": get_activity_summary(),
        "aiChat": get_ai_chat(),
        "aiReview": get_ai_review(),
        "bodyMetrics": get_body_metrics(),
        "homePlan": fetch_all("SELECT icon_key, title, subtitle, status, value_text FROM home_plan_items ORDER BY sort_order"),
        "profileMenus": fetch_all("SELECT icon_key, title, note FROM profile_menu_items ORDER BY sort_order"),
    }
