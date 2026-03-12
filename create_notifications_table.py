import sqlite3

# connect to database
conn = sqlite3.connect("database.db")

# create cursor
cursor = conn.cursor()

# =============================================
# CREATE NOTIFICATIONS TABLE
# This table stores all user notifications
# =============================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

message TEXT,

link TEXT,

is_read INTEGER DEFAULT 0,

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")

print("Notifications table created successfully!")

conn.commit()
conn.close()
