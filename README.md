# NutriTrack

A simple nutrition tracking web app built with Python, Flask and SQLite.

## Features
- Register and log in (passwords are hashed)
- Daily calorie and macro targets worked out from age, height, weight, activity and goal
- Log meals by hand or pick a common food from a built-in list
- Progress bars for today's calories, protein, carbs and fat
- Meal suggestions based on remaining calories and protein
- Weekly charts for calories and protein (Chart.js)
- Veg and non-veg food list, with separate suggestions on the dashboard
- Meal ideas page (31 combinations) filtered by veg / non-veg and meal type, with one-click add
- Light graphics: inline SVG logo, calorie ring and meal icons (no image files)

## How targets are calculated
1. BMR with the Mifflin-St Jeor formula
2. Multiply by an activity factor
3. Add or subtract calories for the goal (lose -400, maintain 0, gain +300)
4. Split calories 25% protein, 50% carbs, 25% fat

## How suggestions work
Foods that fit in the remaining calories are ranked by protein per calorie
(if protein is still needed). The top 4 veg and top 4 non-veg foods are shown
separately.

## Run locally
```
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Deploy on Render
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Set a `SECRET_KEY` environment variable

Note: Render's free tier resets the SQLite file when the service restarts.

Food values in the list are approximate.
