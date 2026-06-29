from __future__ import annotations

import sqlite3
import random
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "techempower.db"

def init_db(db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # World table
    cursor.execute("""
        CREATE TABLE world (
            id INTEGER PRIMARY KEY,
            randomNumber INTEGER NOT NULL
        )
    """)

    # Fortune table
    cursor.execute("""
        CREATE TABLE fortune (
            id INTEGER PRIMARY KEY,
            message TEXT NOT NULL
        )
    """)

    # Insert 10,000 random rows in world
    random.seed(42)  # Seed for reproducibility
    worlds = [(i, random.randint(1, 10000)) for i in range(1, 10001)]
    cursor.executemany("INSERT INTO world (id, randomNumber) VALUES (?, ?)", worlds)

    # Insert fortunes
    fortunes = [
        (1, "fortune: No keyboard present. Press F1 to continue."),
        (2, "Imagine and create."),
        (3, "Remember that the greatest love and the greatest achievements involve great risk."),
        (4, "A journey of a thousand miles begins with a single step."),
        (5, "All your hard work will soon pay off."),
        (6, "You will inherit a large sum of money."),
        (7, "A smooth spade makes a good garden."),
        (8, "The world is your oyster."),
        (9, "Do, or do not. There is no try."),
        (10, "May the Force be with you."),
        (11, "Live long and prosper."),
        (12, "To be or not to be, that is the question.")
    ]
    cursor.executemany("INSERT INTO fortune (id, message) VALUES (?, ?)", fortunes)

    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
