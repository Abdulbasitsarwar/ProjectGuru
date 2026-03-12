import sqlite3
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Meeting slots table with the REQUIRED match_id column
cursor.execute("""
CREATE TABLE IF NOT EXISTS meeting_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,  -- This was missing!
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