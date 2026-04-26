import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# ================= USERS =================
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT,
    level TEXT,
    experience TEXT,
    domain TEXT,
    availability TEXT,
    location TEXT,
    status TEXT
)
""")

# ================= PROFILES =================
c.execute("""
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role TEXT
)
""")

# ================= QUESTIONNAIRES =================
c.execute("""
CREATE TABLE IF NOT EXISTS questionnaires (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    help_areas TEXT
)
""")

# ================= MATCHES =================
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mentor_id, mentee_id)
)
""")

# ================= DECLINED PAIRS =================
c.execute("""
CREATE TABLE IF NOT EXISTS declined_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER,
    mentee_id INTEGER
)
""")

# ================= NOTIFICATIONS =================
c.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    link TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ================= CHAT MESSAGES =================
c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    sender_id INTEGER,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ================= FEEDBACK =================
c.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    from_user INTEGER,
    to_user INTEGER,
    rating INTEGER,
    comment TEXT
)
""")

# ================= MENTOR AVAILABILITY =================
c.execute("""
CREATE TABLE IF NOT EXISTS mentor_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER,
    date TEXT,
    start_time TEXT,
    end_time TEXT
)
""")

# ================= MEETING SLOTS =================
c.execute("""
CREATE TABLE IF NOT EXISTS meeting_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    mentor_id INTEGER,
    mentee_id INTEGER,
    date TEXT,
    start_time TEXT,
    end_time TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

print(" Database fully created for Project GURU")