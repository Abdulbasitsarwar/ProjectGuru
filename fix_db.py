import sqlite3

def update_database():
    # Connect to your database file
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    print("Checking for missing columns...")

    try:
        # Add mentor_notes column
        cursor.execute("ALTER TABLE meeting_slots ADD COLUMN mentor_notes TEXT")
        print("Added column: mentor_notes")
    except sqlite3.OperationalError:
        print("Column mentor_notes already exists.")

    try:
        # Add mentee_notes column
        cursor.execute("ALTER TABLE meeting_slots ADD COLUMN mentee_notes TEXT")
        print("Added column: mentee_notes")
    except sqlite3.OperationalError:
        print("Column mentee_notes already exists.")

    conn.commit()
    conn.close()
    print("Database updated successfully!")

if __name__ == "__main__":
    update_database()