import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Add mentor + mentee profiles for user ID 43
c.execute("INSERT INTO profiles (user_id, role) VALUES (43, 'mentor')")
c.execute("INSERT INTO profiles (user_id, role) VALUES (43, 'mentee')")

conn.commit()
conn.close()

print("✅ Profiles added successfully")
