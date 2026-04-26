import sqlite3

conn = sqlite3.connect("database.db")


try:
    conn.execute("ALTER TABLE users ADD COLUMN verification_code TEXT")
    print("verification_code column added")
except:
    print("verification_code already exists")

try:
    conn.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
    print("is_verified column added")
except:
    print("is_verified already exists")

conn.commit()
conn.close()

print("Database updated successfully ✅")