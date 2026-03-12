import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# USERS
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT,
    level TEXT,
    status TEXT
)
""")

# QUESTIONNAIRES
c.execute("""
CREATE TABLE IF NOT EXISTS questionnaires (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    help_areas TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# MATCHES
c.execute("""
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER,
    mentee_id INTEGER,
    score INTEGER,
    reason TEXT,
    status TEXT DEFAULT 'pending',
    mentor_response TEXT DEFAULT 'pending',
    mentee_response TEXT DEFAULT 'pending',
    FOREIGN KEY (mentor_id) REFERENCES users(id),
    FOREIGN KEY (mentee_id) REFERENCES users(id)
)
""")

conn.commit()
conn.close()

print("✅ Fresh database created")
