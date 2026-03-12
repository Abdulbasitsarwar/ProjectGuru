import sqlite3

conn = sqlite3.connect("database.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS meeting_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    mentor_id INTEGER,
    date TEXT,
    start_time TEXT,
    end_time TEXT,
    booked_by INTEGER,
    status TEXT DEFAULT 'available'
)
""")

conn.commit()
conn.close()

print("New meeting_slots table created successfully!")