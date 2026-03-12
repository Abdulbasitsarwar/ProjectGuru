import sqlite3

conn = sqlite3.connect("database.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    from_user INTEGER,
    to_user INTEGER,
    rating INTEGER,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Feedback table created successfully!")
