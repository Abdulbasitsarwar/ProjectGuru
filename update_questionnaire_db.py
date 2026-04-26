import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Add new columns safely
try:
    cursor.execute("ALTER TABLE questionnaires ADD COLUMN experience TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE questionnaires ADD COLUMN domain TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE questionnaires ADD COLUMN availability TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE questionnaires ADD COLUMN location TEXT")
except:
    pass

conn.commit()
conn.close()

print(" Questionnaire table updated safely.")