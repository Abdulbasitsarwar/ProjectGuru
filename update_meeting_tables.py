import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Mentor availability table
cursor.execute("""
CREATE TABLE IF NOT EXISTS mentor_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER,
    date TEXT,
    start_time TEXT,
    end_time TEXT
)
""")

# Meeting slots table
cursor.execute("""
CREATE TABLE IF NOT EXISTS meeting_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER,
    date TEXT,
    start_time TEXT,
    end_time TEXT,
    mentee_id INTEGER,
    status TEXT DEFAULT 'available'
)
""")

conn.commit()
conn.close()

print("Database updated successfully")