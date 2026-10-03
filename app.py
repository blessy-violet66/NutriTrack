"""
app.py
NutriTrack - Food & Nutrition Tracker
Flask application with session auth, SQLite storage, calorie calculations,
weekly analytics, meal suggestions and supportive nutrition feedback.
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date, timedelta
import datetime as dt

from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = "nutritrack-secret-key-change-in-production"


@app.context_processor
def inject_helpers():
    def format_number(n):
        try:
            if n == 0:
                return "0"
            if float(n) == int(float(n)):
                return f"{int(n):,}"
            return f"{float(n):,.1f}"
        except (ValueError, TypeError):
            return str(n)

    hour = dt.datetime.now().hour
    greeting = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    return dict(format_number=format_number, greeting=greeting, today_label=date.today().strftime("%A, %b %d"))


# ---------------------------------------------------------------------------
# Auth decorator
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ACTIVITY_FACTORS = {
    "Sedentary": 1.2,
    "Lightly Active": 1.375,
    "Moderately Active": 1.55,
    "Very Active": 1.725,
}

GOAL_ADJUSTMENTS = {
    "Maintain Weight": 0,
    "Weight Loss": -400,
    "Weight Gain": 350,
}


def calculate_calorie_target(user):
    """Mifflin-St Jeor equation + activity factor + goal adjustment.
    Returns an integer calorie estimate."""
    weight = float(user["weight"])
    height = float(user["height"])
    age = int(user["age"])
    gender = str(user["gender"]).strip().lower()
    activity_factor = ACTIVITY_FACTORS.get(user["activity_level"], 1.2)

    if gender.startswith("m"):
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    target = bmr * activity_factor + GOAL_ADJUSTMENTS.get(user["goal"], 0)
    return max(1200, int(round(target)))


def macro_targets(calorie_target):
    """Split calories into macro targets (grams).
    Protein 20%, Carbs 50%, Fat 30% of total calories."""
    return {
        "calories": calorie_target,
        "protein": int(round((calorie_target * 0.20) / 4)),
        "carbs": int(round((calorie_target * 0.50) / 4)),
        "fat": int(round((calorie_target * 0.30) / 9)),
        "fiber": 30,
    }


def get_user():
    if "user_id" not in session:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return user


def today_str():
    return date.today().isoformat()


def get_daily_totals(user_id, day):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT calories, protein, carbs, fat, fiber FROM food_entries WHERE user_id = ? AND date = ?",
        (user_id, day),
    ).fetchall()
    conn.close()
    return {
        "calories": round(sum(r["calories"] for r in rows), 1),
        "protein": round(sum(r["protein"] for r in rows), 1),
        "carbs": round(sum(r["carbs"] for r in rows), 1),
        "fat": round(sum(r["fat"] for r in rows), 1),
        "fiber": round(sum(r["fiber"] for r in rows), 1),
    }


def get_today_entries(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM food_entries WHERE user_id = ? AND date = ? ORDER BY id DESC",
        (user_id, today_str()),
    ).fetchall()
    conn.close()
    return rows


def nutrition_status(totals, targets):
    """Classify today's intake relative to the user's target."""
    consumed = totals["calories"]
    target = targets["calories"]
    if target == 0:
        return "balanced"
    pct = consumed / target
    if pct < 0.80:
        return "low"
    if pct > 1.15:
        return "high"
    return "balanced"


def feedback_for_status(status):
    if status == "low":
        return {
            "icon": "⚠️",
            "title": "Your intake is lower than your planned target today.",
            "message": "Make sure you don't skip your next meal. A balanced meal with protein, complex carbohydrates and vegetables can help you stay energized.",
            "suggestion_icon": "🥗",
            "suggestion_title": "Suggested Meal",
            "suggestion": "Paneer + Roti + Vegetable Salad",
            "suggestion_calories": 450,
            "tone": "warning",
        }
    if status == "high":
        return {
            "icon": "⚠️",
            "title": "You've gone above your planned calorie target today.",
            "message": "No worries — one meal doesn't define your progress. For your next meal, consider something lighter and nutrient-rich.",
            "suggestion_icon": "🥗",
            "suggestion_title": "Suggested Next Meal",
            "suggestion": "Vegetable soup + grilled paneer + salad",
            "suggestion_calories": 300,
            "tone": "warning",
        }
    return {
        "icon": "🎉",
        "title": "Great Balance!",
        "message": "You stayed close to your nutrition target today. Keep going!",
        "suggestion_icon": "🏆",
        "suggestion_title": "Nutrition Star",
        "suggestion": "Balanced Day",
        "suggestion_calories": None,
        "tone": "success",
    }


def get_weekly_data(user_id):
    """Return per-day totals for the last 7 days (Mon-Sun of current week)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    days = []
    conn = get_db_connection()
    for i in range(7):
        d = monday + timedelta(days=i)
        d_str = d.isoformat()
        rows = conn.execute(
            "SELECT calories, protein, carbs, fat, fiber FROM food_entries WHERE user_id = ? AND date = ?",
            (user_id, d_str),
        ).fetchall()
        days.append(
            {
                "label": d.strftime("%a"),
                "date": d_str,
                "calories": round(sum(r["calories"] for r in rows), 1),
                "protein": round(sum(r["protein"] for r in rows), 1),
                "carbs": round(sum(r["carbs"] for r in rows), 1),
                "fat": round(sum(r["fat"] for r in rows), 1),
                "fiber": round(sum(r["fiber"] for r in rows), 1),
                "count": len(rows),
            }
        )
    conn.close()
    return days


def weekly_insights(week, target):
    logged = [d for d in week if d["calories"] > 0]
    avg_cal = round(sum(d["calories"] for d in logged) / len(logged), 1) if logged else 0
    avg_protein = round(sum(d["protein"] for d in logged) / len(logged), 1) if logged else 0
    if logged:
        highest = max(logged, key=lambda d: d["calories"])
        lowest = min(logged, key=lambda d: d["calories"])
    else:
        highest = lowest = None
    near_target = sum(1 for d in logged if 0.80 <= (d["calories"] / target) <= 1.15) if target else 0

    # Most frequent meal type this week
    conn = get_db_connection()
    row = conn.execute(
        "SELECT meal_type, COUNT(*) as c FROM food_entries WHERE user_id = ? AND date >= ? GROUP BY meal_type ORDER BY c DESC LIMIT 1",
        (session.get("user_id", -1), week[0]["date"]),
    ).fetchone()
    conn.close()
    frequent_meal = row["meal_type"] if row else "—"

    return {
        "avg_calories": avg_cal,
        "avg_protein": avg_protein,
        "highest_day": highest["label"] if highest else "—",
        "highest_value": highest["calories"] if highest else 0,
        "lowest_day": lowest["label"] if lowest else "—",
        "lowest_value": lowest["calories"] if lowest else 0,
        "near_target_days": near_target,
        "frequent_meal": frequent_meal,
        "logged_days": len(logged),
    }


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password. Please try again.", "error")
        return render_template("login.html")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        height = request.form.get("height", "").strip()
        weight = request.form.get("weight", "").strip()
        activity = request.form.get("activity_level", "").strip()
        goal = request.form.get("goal", "Maintain Weight")

        # Validation
        errors = []
        if not name:
            errors.append("Please enter your full name.")
        if not email or "@" not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm:
            errors.append("Passwords do not match.")
        try:
            age_i = int(age)
            if age_i < 10 or age_i > 120:
                errors.append("Please enter a valid age.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid age.")
            age_i = None
        if gender not in ("Male", "Female", "Other"):
            errors.append("Please select a gender.")
        try:
            height_f = float(height)
            weight_f = float(weight)
            if height_f <= 0 or weight_f <= 0:
                errors.append("Please enter valid height and weight.")
        except (ValueError, TypeError):
            errors.append("Please enter valid height and weight.")
            height_f = weight_f = None
        if activity not in ACTIVITY_FACTORS:
            errors.append("Please select an activity level.")
        if goal not in GOAL_ADJUSTMENTS:
            goal = "Maintain Weight"

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "signup.html",
                form=request.form,
            )

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email already exists. Please login.", "error")
            return render_template("signup.html", form=request.form)

        conn.execute(
            "INSERT INTO users (name, email, password_hash, age, gender, height, weight, activity_level, goal) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                name,
                email,
                generate_password_hash(password),
                age_i,
                gender,
                height_f,
                weight_f,
                activity,
                goal,
            ),
        )
        conn.commit()
        conn.close()
        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html", form={})


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out. See you soon!", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user = get_user()
    targets = macro_targets(calculate_calorie_target(user))
    totals = get_daily_totals(user["id"], today_str())
    entries = get_today_entries(user["id"])
    status = nutrition_status(totals, targets)
    feedback = feedback_for_status(status)

    remaining = max(0, round(targets["calories"] - totals["calories"], 1))

    return render_template(
        "dashboard.html",
        user=user,
        targets=targets,
        totals=totals,
        entries=entries,
        status=status,
        feedback=feedback,
        remaining=remaining,
        active_page="dashboard",
    )


# ---------------------------------------------------------------------------
# Food logging
# ---------------------------------------------------------------------------
@app.route("/add-food", methods=["POST"])
@login_required
def add_food():
    food_name = request.form.get("food_name", "").strip()
    meal_type = request.form.get("meal_type", "").strip()
    calories = request.form.get("calories", "0").strip() or "0"
    protein = request.form.get("protein", "0").strip() or "0"
    carbs = request.form.get("carbs", "0").strip() or "0"
    fat = request.form.get("fat", "0").strip() or "0"
    fiber = request.form.get("fiber", "0").strip() or "0"

    if not food_name:
        flash("Please enter a food name.", "error")
        return redirect(url_for("dashboard"))
    if meal_type not in ("Breakfast", "Lunch", "Snack", "Dinner"):
        flash("Please select a valid meal type.", "error")
        return redirect(url_for("dashboard"))

    try:
        calories = float(calories)
        protein = float(protein)
        carbs = float(carbs)
        fat = float(fat)
        fiber = float(fiber)
    except ValueError:
        flash("Please enter valid numeric nutrition values.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO food_entries (user_id, food_name, meal_type, calories, protein, carbs, fat, fiber, date) VALUES (?,?,?,?,?,?,?, ?,?)",
        (session["user_id"], food_name, meal_type, calories, protein, carbs, fat, fiber, today_str()),
    )
    conn.commit()
    conn.close()
    flash(f"Added {food_name} to your {meal_type}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/delete-food/<int:entry_id>", methods=["POST"])
@login_required
def delete_food(entry_id):
    conn = get_db_connection()
    entry = conn.execute("SELECT * FROM food_entries WHERE id = ? AND user_id = ?", (entry_id, session["user_id"])).fetchone()
    if entry:
        conn.execute("DELETE FROM food_entries WHERE id = ?", (entry_id,))
        conn.commit()
        flash("Food entry deleted.", "success")
    else:
        flash("Entry not found.", "error")
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/edit-food/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_food(entry_id):
    conn = get_db_connection()
    entry = conn.execute("SELECT * FROM food_entries WHERE id = ? AND user_id = ?", (entry_id, session["user_id"])).fetchone()
    if not entry:
        conn.close()
        flash("Entry not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        food_name = request.form.get("food_name", "").strip()
        meal_type = request.form.get("meal_type", "").strip()
        try:
            calories = float(request.form.get("calories", 0) or 0)
            protein = float(request.form.get("protein", 0) or 0)
            carbs = float(request.form.get("carbs", 0) or 0)
            fat = float(request.form.get("fat", 0) or 0)
            fiber = float(request.form.get("fiber", 0) or 0)
        except ValueError:
            flash("Please enter valid numeric values.", "error")
            return render_template("edit_food.html", entry=entry, active_page="dashboard")
        if not food_name or meal_type not in ("Breakfast", "Lunch", "Snack", "Dinner"):
            flash("Please complete food name and meal type.", "error")
            return render_template("edit_food.html", entry=entry, active_page="dashboard")

        conn.execute(
            "UPDATE food_entries SET food_name=?, meal_type=?, calories=?, protein=?, carbs=?, fat=?, fiber=? WHERE id=?",
            (food_name, meal_type, calories, protein, carbs, fat, fiber, entry_id),
        )
        conn.commit()
        conn.close()
        flash("Food entry updated.", "success")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template("edit_food.html", entry=entry, active_page="dashboard")


@app.route("/api/food-database")
@login_required
def api_food_database():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM food_database ORDER BY food_name").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@app.route("/analytics")
@login_required
def analytics():
    user = get_user()
    targets = macro_targets(calculate_calorie_target(user))
    week = get_weekly_data(user["id"])
    insights = weekly_insights(week, targets["calories"])

    return render_template(
        "analytics.html",
        user=user,
        targets=targets,
        week=week,
        insights=insights,
        active_page="analytics",
    )


@app.route("/weekly-summary")
@login_required
def weekly_summary():
    user = get_user()
    targets = macro_targets(calculate_calorie_target(user))
    week = get_weekly_data(user["id"])
    insights = weekly_insights(week, targets["calories"])
    return render_template(
        "weekly_summary.html",
        user=user,
        targets=targets,
        week=week,
        insights=insights,
        active_page="weekly-summary",
    )


# ---------------------------------------------------------------------------
# Meal suggestions
# ---------------------------------------------------------------------------
SUGGESTED_MEALS = [
    {"name": "Paneer Roti Bowl", "meal_type": "Dinner", "calories": 450, "protein": 25, "carbs": 48, "fat": 15, "fiber": 5, "icon": "🥗"},
    {"name": "Vegetable Soup + Grilled Paneer + Salad", "meal_type": "Dinner", "calories": 300, "protein": 18, "carbs": 20, "fat": 12, "fiber": 6, "icon": "🥣"},
    {"name": "Oats + Banana + Milk", "meal_type": "Breakfast", "calories": 320, "protein": 12, "carbs": 52, "fat": 8, "fiber": 6, "icon": "🥣"},
    {"name": "Dal + Rice + Curd", "meal_type": "Lunch", "calories": 420, "protein": 18, "carbs": 65, "fat": 8, "fiber": 6, "icon": "🍛"},
    {"name": "2 Eggs + Toast", "meal_type": "Breakfast", "calories": 320, "protein": 18, "carbs": 28, "fat": 14, "fiber": 2, "icon": "🍳"},
    {"name": "Chicken + Vegetables", "meal_type": "Lunch", "calories": 380, "protein": 35, "carbs": 15, "fat": 18, "fiber": 4, "icon": "🍗"},
    {"name": "Mixed Nuts + Apple", "meal_type": "Snack", "calories": 280, "protein": 7, "carbs": 30, "fat": 16, "fiber": 7, "icon": "🍎"},
    {"name": "Vegetable Salad Bowl", "meal_type": "Snack", "calories": 150, "protein": 5, "carbs": 20, "fat": 4, "fiber": 6, "icon": "🥗"},
]


@app.route("/meal-suggestions")
@login_required
def meal_suggestions():
    user = get_user()
    targets = macro_targets(calculate_calorie_target(user))
    totals = get_daily_totals(user["id"], today_str())
    remaining = max(0, round(targets["calories"] - totals["calories"], 1))

    # Rank suggestions: prefer those that fit within remaining calories,
    # and that fill macro gaps (protein low => protein-rich pick).
    protein_gap = targets["protein"] - totals["protein"]
    ranked = sorted(
        SUGGESTED_MEALS,
        key=lambda m: (
            0 if m["calories"] <= remaining + 50 else 1,  # fit first
            -m["protein"] if protein_gap > 0 else 0,       # protein-rich when gap
            m["calories"],                                 # lighter first
        ),
    )

    return render_template(
        "suggestions.html",
        user=user,
        targets=targets,
        totals=totals,
        remaining=remaining,
        suggestions=ranked,
        active_page="meal-suggestions",
    )


@app.route("/add-suggested-meal", methods=["POST"])
@login_required
def add_suggested_meal():
    name = request.form.get("food_name", "").strip()
    meal_type = request.form.get("meal_type", "Snack").strip()
    calories = request.form.get("calories", "0")
    protein = request.form.get("protein", "0")
    carbs = request.form.get("carbs", "0")
    fat = request.form.get("fat", "0")
    fiber = request.form.get("fiber", "0")
    if not name:
        flash("Invalid suggestion.", "error")
        return redirect(url_for("meal_suggestions"))
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO food_entries (user_id, food_name, meal_type, calories, protein, carbs, fat, fiber, date) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                session["user_id"],
                name,
                meal_type if meal_type in ("Breakfast", "Lunch", "Snack", "Dinner") else "Snack",
                float(calories or 0),
                float(protein or 0),
                float(carbs or 0),
                float(fat or 0),
                float(fiber or 0),
                today_str(),
            ),
        )
        conn.commit()
        conn.close()
        flash(f"Added {name} to your food log.", "success")
    except ValueError:
        flash("Could not add that meal.", "error")
    return redirect(url_for("meal_suggestions"))


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        height = request.form.get("height", "").strip()
        weight = request.form.get("weight", "").strip()
        activity = request.form.get("activity_level", "").strip()
        goal = request.form.get("goal", "Maintain Weight")

        try:
            age_i = int(age)
            height_f = float(height)
            weight_f = float(weight)
        except (ValueError, TypeError):
            flash("Please enter valid numeric values for age, height and weight.", "error")
            conn.close()
            return redirect(url_for("profile"))

        if not name or gender not in ("Male", "Female", "Other") or activity not in ACTIVITY_FACTORS:
            flash("Please complete all required fields.", "error")
            conn.close()
            return redirect(url_for("profile"))

        conn.execute(
            "UPDATE users SET name=?, age=?, gender=?, height=?, weight=?, activity_level=?, goal=? WHERE id=?",
            (name, age_i, gender, height_f, weight_f, activity, goal, session["user_id"]),
        )
        conn.commit()
        session["user_name"] = name
        flash("Profile updated successfully.", "success")
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    conn.close()
    calorie_target = calculate_calorie_target(user)
    targets = macro_targets(calorie_target)
    return render_template("profile.html", user=user, calorie_target=calorie_target, targets=targets, active_page="profile")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)