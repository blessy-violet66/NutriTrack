# NutriTrack – Food & Nutrition Tracker

> Eat Better. Track Smarter. Feel Better.

NutriTrack is a personal food, calorie and nutrition tracking web app. Users create an account, log their daily meals, monitor calories and macro nutrients, view weekly analytics with interactive charts, and receive supportive, personalized feedback based on their intake.

Built as a beginner-friendly full-stack project suitable for a college submission, GitHub portfolio, and resume.

---

## Overview

NutriTrack helps users build healthier eating habits by making food logging simple and insightful. It calculates a personalized daily calorie target from the user's profile, tracks meals in real time, visualizes weekly patterns with Chart.js, and offers encouraging, non-judgmental feedback — never shaming the user for going over or under their target.

### Key highlights

- Secure signup & login with hashed passwords
- Personalized calorie target based on age, gender, height, weight, activity level and goal
- Quick-add food logging with a built-in approximate nutrition database
- Live daily nutrition dashboard with progress ring and macro bars
- Weekly analytics with line, bar and donut charts (Chart.js)
- Intelligent nutrition status: **Low**, **Balanced**, or **High** intake
- Smart meal suggestions ranked by remaining calories and macro gaps
- Playful confetti celebration on balanced days
- Fully responsive — sidebar on desktop, collapsible on mobile
- Glassmorphism UI with soft shadows, gradients and micro-animations

---

## Features

| Feature | Description |
|---|---|
| **Authentication** | Signup, login, logout with Werkzeug password hashing and Flask sessions |
| **Dashboard** | Summary cards (calories, protein, carbs, fats), circular progress ring, macro bars |
| **Food Logging** | Add, edit, delete food entries with meal type and full nutrition fields |
| **Built-in Food Database** | 20 common foods (rice, roti, idli, eggs, chicken, paneer, etc.) with auto-fill |
| **Nutrition Status** | Classifies the day as Low / Balanced / High relative to the user's target |
| **Meal Suggestions** | Ranks suggested meals by remaining calories and protein gap; one-click add |
| **Weekly Analytics** | Line charts for calories, protein, carbs, fat + macro donut breakdown |
| **Weekly Summary** | Auto-calculated insights: averages, highest/lowest day, consistency, frequent meal |
| **Profile** | View and update personal details; see estimated calorie target and macro split |
| **Responsive Design** | Desktop sidebar, tablet grid, mobile collapsible sidebar |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python Flask |
| Database | SQLite |
| Charts | Chart.js |
| Icons | Lucide |
| Fonts | Plus Jakarta Sans, Nunito (Google Fonts) |
| Password Security | Werkzeug `generate_password_hash` / `check_password_hash` |

---

## Project Architecture

```
nutritrack/
│
├── app.py                 # Flask app: routes, auth, calculations, logic
├── database.py            # SQLite connection + schema + seed data
├── requirements.txt       # Python dependencies
├── README.md
│
├── templates/
│   ├── base.html          # Shared layout (head, toasts, scripts)
│   ├── index.html         # Landing page
│   ├── login.html         # Login page
│   ├── signup.html        # Signup page
│   ├── dashboard.html     # Main dashboard
│   ├── edit_food.html     # Edit food entry
│   ├── analytics.html     # Weekly analytics + charts
│   ├── weekly_summary.html# Weekly insights + day cards
│   ├── suggestions.html   # Meal suggestions
│   ├── profile.html       # User profile + calorie target
│   └── partials/
│       ├── _sidebar.html  # Sidebar navigation
│       └── _topbar.html   # Top navbar with greeting
│
├── static/
│   ├── css/
│   │   └── style.css      # Full stylesheet
│   ├── js/
│   │   └── script.js      # Frontend interactions + Chart.js
│   └── images/
│
└── database/
    └── nutritrack.db      # SQLite database (auto-created)
```

---

## Database Design

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| name | TEXT | Full name |
| email | TEXT | Unique |
| password_hash | TEXT | Werkzeug-hashed |
| age | INTEGER | |
| gender | TEXT | Male / Female / Other |
| height | REAL | cm |
| weight | REAL | kg |
| activity_level | TEXT | Sedentary / Lightly / Moderately / Very Active |
| goal | TEXT | Maintain / Loss / Gain |

### `food_entries`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK | → users.id |
| food_name | TEXT | |
| meal_type | TEXT | Breakfast / Lunch / Snack / Dinner |
| calories | REAL | kcal |
| protein | REAL | g |
| carbs | REAL | g |
| fat | REAL | g |
| fiber | REAL | g |
| date | TEXT | ISO date (YYYY-MM-DD) |

### `food_database`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| food_name | TEXT | |
| calories | REAL | per serving |
| protein | REAL | g |
| carbs | REAL | g |
| fat | REAL | g |
| fiber | REAL | g |

---

## How It Works

### 1. Calorie Target Calculation
Uses the **Mifflin-St Jeor equation** for BMR, multiplied by an activity factor, then adjusted by goal:

- **BMR (Male)** = `10 × weight + 6.25 × height − 5 × age + 5`
- **BMR (Female)** = `10 × weight + 6.25 × height − 5 × age − 161`
- **TDEE** = BMR × activity factor (1.2 / 1.375 / 1.55 / 1.725)
- **Target** = TDEE + goal adjustment (−400 for loss, +350 for gain, 0 for maintain)

Macro split: Protein 20%, Carbs 50%, Fat 30% of total calories.

### 2. Nutrition Status
Today's calories are compared to the target:
- **Low**: intake < 80% of target
- **Balanced**: 80%–115% of target
- **High**: intake > 115% of target

Each status shows a supportive message and a suggested next meal — never shaming language.

### 3. Weekly Analytics
All charts use the user's actual stored food entries grouped by day for the current week (Monday–Sunday). No random or fake data is used once the user starts logging.

### 4. Authentication
Passwords are hashed with Werkzeug's PBKDF2 implementation. Flask sessions store the user ID. A `@login_required` decorator protects all app routes. Users can only see and modify their own food entries.

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Steps

```bash
# 1. Clone or download the project
git clone <your-repo-url>
cd nutritrack

# 2. (Recommended) Create a virtual environment
python -m venv venv

# Activate it:
#   Windows:  venv\Scripts\activate
#   macOS/Linux:  source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

The app starts on **http://localhost:5000**.

The SQLite database (`database/nutritrack.db`) is created automatically on first run, and the built-in food database is seeded with 20 common foods.

---

## How to Run

```bash
python app.py
```

Then open your browser to `http://localhost:5000`.

1. Click **Get Started** and create an account.
2. Fill in your profile details (age, gender, height, weight, activity level, goal).
3. Log in — you'll see your personalized dashboard.
4. Click **Add Food** to log a meal. Try selecting a food from the built-in list for auto-fill.
5. Watch your progress ring, macro bars and nutrition status update.
6. Explore **Nutrition Analytics** and **Weekly Summary** as you log more meals.
7. Visit **Meal Suggestions** for ideas that fit your remaining calories.

---

## Sample Food Data

The built-in food database includes approximate per-serving values:

| Food | Calories | Protein | Carbs | Fat | Fiber |
|---|---|---|---|---|---|
| Rice (1 cup) | 205 | 4 | 45 | 1 | 0 |
| Roti (1 piece) | 120 | 3 | 18 | 3 | 1 |
| Idli (2 pieces) | 120 | 4 | 24 | 1 | 1 |
| Dosa (1 plain) | 133 | 3 | 18 | 4 | 1 |
| Oats (1 bowl) | 154 | 5 | 27 | 3 | 4 |
| Banana | 105 | 1 | 27 | 0 | 3 |
| Apple | 95 | 0 | 25 | 0 | 4 |
| Egg (1 whole) | 72 | 6 | 0 | 5 | 0 |
| Chicken (100g) | 165 | 31 | 0 | 4 | 0 |
| Paneer (100g) | 265 | 18 | 3 | 20 | 0 |
| Dal (1 bowl) | 150 | 9 | 22 | 3 | 6 |
| Milk (1 cup) | 150 | 8 | 12 | 5 | 0 |
| Mixed Nuts (30g) | 180 | 6 | 6 | 16 | 3 |
| Vegetable Soup | 90 | 3 | 14 | 2 | 3 |

> Values are approximate and labelled as such in the UI. Users can modify any value before saving.

---

## Screenshots

> _Add screenshots here after running the app — landing page, dashboard, analytics, suggestions, profile._

```
screenshots/
├── landing.png
├── dashboard.png
├── analytics.png
├── suggestions.png
└── profile.png
```

---

## Future Enhancements

- Water intake tracking
- Custom food database entries per user
- Barcode / packaged food scanning
- Activity and exercise logging
- Export weekly reports as PDF
- Dark mode
- Multi-language support
- Progressive Web App (PWA) with offline support
- Goal progress tracking over weeks/months

---

## Disclaimer

Calorie needs vary between individuals. The estimated daily target is for tracking purposes only and is **not medical advice**. Always consult a qualified healthcare professional or registered dietitian for personalized nutrition guidance.

---

## License

This project is open-source and free to use for educational purposes.
