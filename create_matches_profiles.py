import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS matches_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_profile_id INTEGER,
    mentee_profile_id INTEGER,
    score INTEGER,
    reason TEXT,
    status TEXT DEFAULT 'pending',
    mentor_response TEXT DEFAULT 'pending',
    mentee_response TEXT DEFAULT 'pending',
    FOREIGN KEY (mentor_profile_id) REFERENCES profiles(id),
    FOREIGN KEY (mentee_profile_id) REFERENCES profiles(id)
)
""")

conn.commit()
conn.close()

print("✅ Profile-based matches table created")