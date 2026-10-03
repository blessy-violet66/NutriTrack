"""
database.py
Handles SQLite connection and schema for NutriTrack.

Tables:
- users         : profile + hashed password
- food_entries  : per-user daily food logs
- food_database : built-in approximate nutrition values for common foods
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "nutritrack.db")


def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# Built-in approximate nutrition per serving (100 kcal-ish servings).
# Values are approximate and clearly labelled as such in the UI.
BUILTIN_FOODS = [
    ("Rice (1 cup cooked)", 205, 4, 45, 1, 0),
    ("Roti (1 piece)", 120, 3, 18, 3, 1),
    ("Idli (2 pieces)", 120, 4, 24, 1, 1),
    ("Dosa (1 plain)", 133, 3, 18, 4, 1),
    ("Upma (1 bowl)", 192, 5, 30, 6, 1),
    ("Oats (1 bowl cooked)", 154, 5, 27, 3, 4),
    ("Banana (1 medium)", 105, 1, 27, 0, 3),
    ("Apple (1 medium)", 95, 0, 25, 0, 4),
    ("Egg (1 whole)", 72, 6, 0, 5, 0),
    ("Chicken (100g grilled)", 165, 31, 0, 4, 0),
    ("Paneer (100g)", 265, 18, 3, 20, 0),
    ("Dal (1 bowl)", 150, 9, 22, 3, 6),
    ("Curd (1 cup)", 100, 7, 10, 3, 0),
    ("Milk (1 cup)", 150, 8, 12, 5, 0),
    ("Mixed Vegetables (1 cup)", 80, 3, 15, 1, 5),
    ("Mixed Nuts (30g)", 180, 6, 6, 16, 3),
    ("Vegetable Soup (1 bowl)", 90, 3, 14, 2, 3),
    ("Grilled Paneer Salad", 320, 20, 12, 22, 5),
    ("Paneer Roti Bowl", 450, 25, 48, 15, 5),
    ("Vegetable Salad Bowl", 150, 5, 20, 4, 6),
]


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            height REAL NOT NULL,
            weight REAL NOT NULL,
            activity_level TEXT NOT NULL,
            goal TEXT NOT NULL DEFAULT 'Maintain Weight'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS food_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            fiber REAL NOT NULL DEFAULT 0,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS food_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_name TEXT NOT NULL,
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            fiber REAL NOT NULL DEFAULT 0
        )
        """
    )

    # Seed built-in foods only if the table is empty.
    cur.execute("SELECT COUNT(*) FROM food_database")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO food_database (food_name, calories, protein, carbs, fat, fiber) VALUES (?,?,?,?,?,?)",
            BUILTIN_FOODS,
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH)
