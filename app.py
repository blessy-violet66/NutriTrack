import os
import sqlite3
from datetime import date, timedelta
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, g, abort)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nutritrack-blessy-2026")
DATABASE = os.path.join(os.path.dirname(__file__), "nutritrack.db")

# ---------- database ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# name, serving, calories, protein, carbs, fat, category, icon
# (values are approximate, per serving)
FOODS = [
    # ----- veg -----
    ("Idli", "2 pieces", 130, 4, 26, 0.4, "veg", "🍘"),
    ("Plain dosa", "1 dosa", 133, 2.7, 22, 3.7, "veg", "🥞"),
    ("Besan chilla", "1 piece", 100, 6, 12, 3, "veg", "🥞"),
    ("Chapati", "1 piece", 104, 3, 18, 2.5, "veg", "🫓"),
    ("Cooked rice", "1 cup", 205, 4.3, 45, 0.4, "veg", "🍚"),
    ("Dal", "1 bowl", 150, 9, 22, 3, "veg", "🥣"),
    ("Sambar", "1 bowl", 120, 6, 18, 3, "veg", "🥣"),
    ("Poha", "1 plate", 250, 5, 45, 6, "veg", "🍲"),
    ("Upma", "1 bowl", 210, 5, 30, 8, "veg", "🍲"),
    ("Veg khichdi", "1 bowl", 220, 8, 38, 4, "veg", "🍲"),
    ("Paneer", "100 g", 265, 18, 1.2, 20, "veg", "🧀"),
    ("Tofu", "100 g", 76, 8, 1.9, 4.8, "veg", "🧊"),
    ("Soya chunks", "30 g dry", 104, 16, 10, 0.3, "veg", "🌱"),
    ("Boiled chickpeas", "1 cup", 269, 14.5, 45, 4.2, "veg", "🌱"),
    ("Sprouts salad", "1 bowl", 120, 8, 20, 1, "veg", "🥗"),
    ("Roasted chana", "30 g", 110, 6, 18, 2, "veg", "🌰"),
    ("Curd", "1 cup", 149, 8.5, 11.4, 8, "veg", "🥛"),
    ("Buttermilk", "1 glass", 40, 2, 5, 1, "veg", "🥛"),
    ("Milk", "1 cup", 150, 8, 12, 8, "veg", "🥛"),
    ("Oats (cooked)", "1 cup", 154, 6, 27, 3, "veg", "🥣"),
    ("Banana", "1 medium", 105, 1.3, 27, 0.4, "veg", "🍌"),
    ("Apple", "1 medium", 95, 0.5, 25, 0.3, "veg", "🍎"),
    ("Orange", "1 medium", 62, 1.2, 15, 0.2, "veg", "🍊"),
    ("Peanuts", "30 g", 170, 7, 5, 14, "veg", "🥜"),
    ("Almonds", "10 pieces", 70, 2.5, 2.5, 6, "veg", "🌰"),
    ("Bread slice", "1 slice", 80, 3, 14, 1, "veg", "🍞"),
    ("Peanut butter", "1 tbsp", 94, 4, 3, 8, "veg", "🥜"),
    ("Veg biryani", "1 plate", 290, 6, 45, 9, "veg", "🍛"),
    # ----- non-veg -----
    ("Boiled egg", "1 egg", 78, 6.3, 0.6, 5.3, "nonveg", "🥚"),
    ("Omelette", "2 eggs", 190, 12.6, 1.5, 14, "nonveg", "🍳"),
    ("Chicken breast (grilled)", "100 g", 165, 31, 0, 3.6, "nonveg", "🍗"),
    ("Chicken curry", "1 bowl", 220, 28, 6, 10, "nonveg", "🍗"),
    ("Chicken tikka", "4 pieces", 200, 28, 4, 8, "nonveg", "🍢"),
    ("Fish curry", "1 bowl", 200, 22, 5, 10, "nonveg", "🐟"),
    ("Grilled fish", "100 g", 130, 22, 0, 4, "nonveg", "🐟"),
    ("Prawns (cooked)", "100 g", 99, 24, 0.2, 0.3, "nonveg", "🍤"),
    ("Egg curry", "1 bowl", 230, 13, 6, 17, "nonveg", "🥘"),
    ("Chicken biryani", "1 plate", 400, 22, 48, 14, "nonveg", "🍛"),
]

# Full meal ideas (combinations). Values are approximate.
# name, what is in it, calories, protein, carbs, fat, category, meal type, icon
IDEAS_RAW = [
    # ----- veg -----
    ("Idli and sambar", "3 idli with 1 bowl sambar", 315, 12, 57, 4, "veg", "Breakfast", "🍘"),
    ("Oats with banana", "1 cup oats cooked in milk, 1 banana", 410, 15, 66, 11, "veg", "Breakfast", "🥣"),
    ("Besan chilla and curd", "2 chilla with 1 cup curd", 350, 21, 35, 14, "veg", "Breakfast", "🥞"),
    ("Peanut butter toast", "2 bread slices, 1 tbsp peanut butter, 1 banana", 360, 11, 58, 10, "veg", "Breakfast", "🍞"),
    ("Poha with peanuts", "1 plate poha, a few peanuts, 1 glass buttermilk", 300, 8, 48, 8, "veg", "Breakfast", "🍲"),
    ("Rice, dal and curd", "1 cup rice, 1 bowl dal, 1 cup curd", 505, 22, 78, 11, "veg", "Lunch", "🍚"),
    ("Chapati and paneer curry", "2 chapati with 100 g paneer", 475, 24, 37, 25, "veg", "Lunch", "🧀"),
    ("Chickpea salad bowl", "1 cup chickpeas with cucumber, tomato, onion", 300, 15, 50, 5, "veg", "Lunch", "🥗"),
    ("Veg biryani and raita", "1 plate biryani, 1 cup curd", 440, 15, 56, 17, "veg", "Lunch", "🍛"),
    ("Soya curry and chapati", "2 chapati with 1 bowl soya chunks curry", 390, 24, 46, 11, "veg", "Lunch", "🌱"),
    ("Roasted chana and apple", "30 g roasted chana, 1 apple", 205, 7, 43, 2, "veg", "Snack", "🌰"),
    ("Peanuts and banana", "30 g peanuts, 1 banana", 275, 8, 32, 14, "veg", "Snack", "🥜"),
    ("Curd with almonds", "1 cup curd, 10 almonds", 220, 11, 14, 14, "veg", "Snack", "🥛"),
    ("Sprouts chaat", "1 bowl sprouts with onion, tomato, lemon", 150, 9, 22, 2, "veg", "Snack", "🥗"),
    ("Chapati and dal", "2 chapati with 1 bowl dal", 360, 15, 58, 8, "veg", "Dinner", "🫓"),
    ("Veg khichdi and curd", "1 bowl khichdi, 1 cup curd", 370, 17, 49, 12, "veg", "Dinner", "🍲"),
    ("Sambar rice", "1 cup rice with 1 bowl sambar", 325, 10, 63, 3, "veg", "Dinner", "🍚"),
    ("Tofu stir fry with rice", "100 g tofu with vegetables, 1 cup rice", 340, 15, 50, 8, "veg", "Dinner", "🥘"),
    # ----- non-veg -----
    ("Boiled eggs and toast", "2 boiled eggs, 2 bread slices", 316, 19, 29, 13, "nonveg", "Breakfast", "🥚"),
    ("Omelette and chapati", "2 egg omelette, 1 chapati", 295, 16, 20, 17, "nonveg", "Breakfast", "🍳"),
    ("Chicken curry and rice", "1 bowl chicken curry, 1 cup rice", 425, 32, 51, 10, "nonveg", "Lunch", "🍗"),
    ("Egg curry and chapati", "1 bowl egg curry, 2 chapati", 440, 19, 42, 22, "nonveg", "Lunch", "🥘"),
    ("Grilled chicken salad", "120 g grilled chicken with vegetables", 270, 38, 8, 9, "nonveg", "Lunch", "🥗"),
    ("Fish curry and rice", "1 bowl fish curry, 1 cup rice", 405, 26, 50, 10, "nonveg", "Lunch", "🐟"),
    ("Chicken biryani", "1 plate chicken biryani", 400, 22, 48, 14, "nonveg", "Lunch", "🍛"),
    ("Egg and banana", "1 boiled egg, 1 banana", 185, 8, 28, 6, "nonveg", "Snack", "🥚"),
    ("Chicken tikka", "4 pieces chicken tikka", 200, 28, 4, 8, "nonveg", "Snack", "🍢"),
    ("Chicken curry and chapati", "1 bowl chicken curry, 2 chapati", 430, 34, 42, 15, "nonveg", "Dinner", "🍗"),
    ("Egg bhurji and chapati", "2 egg bhurji, 2 chapati", 420, 19, 39, 20, "nonveg", "Dinner", "🍳"),
    ("Fish fry and chapati", "100 g fish fry, 1 chapati, salad", 300, 23, 24, 12, "nonveg", "Dinner", "🐟"),
    ("Prawns with rice", "100 g prawns, 1 cup rice, vegetables", 330, 28, 48, 4, "nonveg", "Dinner", "🍤"),
]
IDEA_KEYS = ["name", "items", "calories", "protein", "carbs", "fat",
             "category", "meal_type", "icon"]
MEAL_IDEAS = [dict(zip(IDEA_KEYS, row), id=i)
              for i, row in enumerate(IDEAS_RAW)]


def init_db():
    db = sqlite3.connect(DATABASE)
    # older versions of the foods table had no category column
    columns = [row[1] for row in db.execute("PRAGMA table_info(foods)")]
    if columns and "category" not in columns:
        db.execute("DROP TABLE foods")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        age INTEGER, gender TEXT, height_cm REAL, weight_kg REAL,
        activity TEXT, goal TEXT,
        calorie_target INTEGER, protein_target INTEGER,
        carbs_target INTEGER, fat_target INTEGER
    );
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        meal_type TEXT,
        calories REAL, protein REAL, carbs REAL, fat REAL,
        meal_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, serving TEXT,
        calories REAL, protein REAL, carbs REAL, fat REAL,
        category TEXT, icon TEXT
    );
    """)
    # keep the foods table in step with the FOODS list above
    if db.execute("SELECT COUNT(*) FROM foods").fetchone()[0] != len(FOODS):
        db.execute("DELETE FROM foods")
        db.executemany(
            "INSERT INTO foods (name, serving, calories, protein, carbs, fat, "
            "category, icon) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", FOODS)
    db.commit()
    db.close()


# ---------- helpers ----------

ACTIVITY = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}
GOAL_ADJUST = {"lose": -400, "maintain": 0, "gain": 300}


def calculate_targets(age, gender, height, weight, activity, goal):
    """Mifflin-St Jeor BMR -> daily calories -> macro split 25/50/25."""
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    calories = max(1200, round(bmr * ACTIVITY[activity] + GOAL_ADJUST[goal]))
    protein = round(calories * 0.25 / 4)
    carbs = round(calories * 0.50 / 4)
    fat = round(calories * 0.25 / 9)
    return calories, protein, carbs, fat


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        user = get_db().execute(
            "SELECT id FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        if user is None:
            session.clear()
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    return get_db().execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()


def day_totals(db, user_id, day):
    row = db.execute(
        "SELECT COALESCE(SUM(calories),0) c, COALESCE(SUM(protein),0) p, "
        "COALESCE(SUM(carbs),0) cb, COALESCE(SUM(fat),0) f "
        "FROM meals WHERE user_id = ? AND meal_date = ?",
        (user_id, day)).fetchone()
    return {"calories": row["c"], "protein": row["p"],
            "carbs": row["cb"], "fat": row["f"]}


def get_suggestions(db, remaining_cal, remaining_protein, category, limit=4):
    """Suggest foods of one category (veg / nonveg) that fit in the
    remaining calories. If protein is still needed, pick the highest
    protein per calorie first."""
    if remaining_cal < 60:
        return []
    foods = db.execute(
        "SELECT * FROM foods WHERE category = ? AND calories <= ?",
        (category, remaining_cal)).fetchall()
    if remaining_protein > 5:
        foods = sorted(foods, key=lambda f: f["protein"] / f["calories"],
                       reverse=True)
    else:
        foods = sorted(foods, key=lambda f: f["calories"])
    return foods[:limit]


def percent(value, target):
    if not target:
        return 0
    return min(100, round(value / target * 100))


# ---------- auth ----------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        try:
            age = int(request.form["age"])
            height = float(request.form["height"])
            weight = float(request.form["weight"])
        except ValueError:
            flash("Age, height and weight must be numbers.")
            return render_template("register.html")
        gender = request.form["gender"]
        activity = request.form["activity"]
        goal = request.form["goal"]

        if not username or len(password) < 4:
            flash("Enter a username and a password of at least 4 characters.")
            return render_template("register.html")

        cal, pro, carb, fat = calculate_targets(
            age, gender, height, weight, activity, goal)
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password_hash, age, gender, "
                "height_cm, weight_kg, activity, goal, calorie_target, "
                "protein_target, carbs_target, fat_target) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (username, generate_password_hash(password), age, gender,
                 height, weight, activity, goal, cal, pro, carb, fat))
            db.commit()
        except sqlite3.IntegrityError:
            flash("That username is already taken.")
            return render_template("register.html")
        flash("Account created. Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?",
            (request.form["username"].strip(),)).fetchone()
        if user and check_password_hash(user["password_hash"],
                                        request.form["password"]):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        flash("Wrong username or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- main pages ----------

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user = current_user()
    today = date.today().isoformat()
    totals = day_totals(db, user["id"], today)
    meals = db.execute(
        "SELECT * FROM meals WHERE user_id = ? AND meal_date = ? ORDER BY id",
        (user["id"], today)).fetchall()

    remaining_cal = user["calorie_target"] - totals["calories"]
    remaining_pro = user["protein_target"] - totals["protein"]
    veg_suggestions = get_suggestions(db, remaining_cal, remaining_pro, "veg")
    nonveg_suggestions = get_suggestions(db, remaining_cal, remaining_pro, "nonveg")

    bars = {
        "Calories": (totals["calories"], user["calorie_target"], "kcal"),
        "Protein": (totals["protein"], user["protein_target"], "g"),
        "Carbs": (totals["carbs"], user["carbs_target"], "g"),
        "Fat": (totals["fat"], user["fat_target"], "g"),
    }
    return render_template(
        "dashboard.html", user=user, meals=meals, bars=bars,
        percent=percent, veg_suggestions=veg_suggestions,
        nonveg_suggestions=nonveg_suggestions,
        remaining_cal=round(remaining_cal), remaining_pro=round(remaining_pro),
        today=today)


@app.route("/ideas")
@login_required
def ideas():
    diet = request.args.get("diet", "all")
    meal_type = request.args.get("type", "all")
    db = get_db()
    user = current_user()
    totals = day_totals(db, user["id"], date.today().isoformat())
    remaining = user["calorie_target"] - totals["calories"]

    shown = [i for i in MEAL_IDEAS
             if meal_type == "all" or i["meal_type"] == meal_type]
    veg = [i for i in shown if i["category"] == "veg"]
    nonveg = [i for i in shown if i["category"] == "nonveg"]
    return render_template("ideas.html", veg=veg, nonveg=nonveg, diet=diet,
                           meal_type=meal_type, remaining=round(remaining))


@app.route("/add_idea/<int:idea_id>", methods=["POST"])
@login_required
def add_idea(idea_id):
    if idea_id < 0 or idea_id >= len(MEAL_IDEAS):
        abort(404)
    idea = MEAL_IDEAS[idea_id]
    db = get_db()
    db.execute(
        "INSERT INTO meals (user_id, name, meal_type, calories, protein, "
        "carbs, fat, meal_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (session["user_id"], idea["name"], idea["meal_type"],
         idea["calories"], idea["protein"], idea["carbs"], idea["fat"],
         date.today().isoformat()))
    db.commit()
    flash("Added " + idea["name"] + " to today.")
    return redirect(url_for("dashboard"))


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_meal():
    db = get_db()
    if request.method == "POST":
        try:
            calories = float(request.form["calories"])
            protein = float(request.form["protein"] or 0)
            carbs = float(request.form["carbs"] or 0)
            fat = float(request.form["fat"] or 0)
        except ValueError:
            flash("Please enter numbers for calories and macros.")
            return redirect(url_for("add_meal"))
        db.execute(
            "INSERT INTO meals (user_id, name, meal_type, calories, protein, "
            "carbs, fat, meal_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (session["user_id"], request.form["name"].strip(),
             request.form["meal_type"], calories, protein, carbs, fat,
             date.today().isoformat()))
        db.commit()
        return redirect(url_for("dashboard"))
    foods = db.execute("SELECT * FROM foods ORDER BY name").fetchall()
    return render_template("add_meal.html", foods=foods)


@app.route("/delete/<int:meal_id>", methods=["POST"])
@login_required
def delete_meal(meal_id):
    db = get_db()
    db.execute("DELETE FROM meals WHERE id = ? AND user_id = ?",
               (meal_id, session["user_id"]))
    db.commit()
    return redirect(url_for("dashboard"))


@app.route("/weekly")
@login_required
def weekly():
    db = get_db()
    user = current_user()
    labels, calories, protein = [], [], []
    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i)
        totals = day_totals(db, user["id"], day.isoformat())
        labels.append(day.strftime("%a %d"))
        calories.append(round(totals["calories"]))
        protein.append(round(totals["protein"]))
    logged_days = [c for c in calories if c > 0]
    average = round(sum(logged_days) / len(logged_days)) if logged_days else 0
    return render_template(
        "weekly.html", user=user, labels=labels, calories=calories,
        protein=protein, average=average, days_logged=len(logged_days))


init_db()

if __name__ == "__main__":
    app.run(debug=True)