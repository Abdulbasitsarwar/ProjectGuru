import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Add mentor_response column
try:
    cursor.execute("ALTER TABLE matches ADD COLUMN mentor_response TEXT")
except:
    pass

# Add mentee_response column
try:
    cursor.execute("ALTER TABLE matches ADD COLUMN mentee_response TEXT")
except:
    pass

conn.commit()
conn.close()

print(" Matches table updated successfully")
