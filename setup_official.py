import sqlite3

def factory_reset_and_seed():
    conn = sqlite3.connect("database.db")
    
    print(" Initiating Factory Reset...")
    
    # 1. WIPE ALL DATA CLEAN
    # This empties every table so you start with a completely fresh system
    tables_to_clear = [
        "users", "profiles", "questionnaires", "matches", 
        "declined_pairs", "meeting_slots", "mentor_availability", 
        "feedback", "notifications", "messages"
    ]
    
    for table in tables_to_clear:
        try:
            conn.execute(f"DELETE FROM {table}")
        except sqlite3.OperationalError:
            pass # Skips safely if a table happens to not exist yet
            
    print(" Database wiped clean.")
    print(" Creating official Aston University accounts...")
    
    # ====================================================
    # 2. OFFICIAL ACCOUNTS DATA
    # Format: (email, role, domain, experience, location, help_areas)
    # ====================================================
    official_users = [
        # --- MENTORS (Staff/Senior Alumni) ---
        ("dr.smith@aston.ac.uk", "mentor", "computer science", "10+ years", "birmingham", "python, ai, architecture"),
        ("prof.jones@aston.ac.uk", "mentor", "business", "10+ years", "london", "finance, leadership, strategy"),
        ("j.doe@aston.ac.uk", "mentor", "cybersecurity", "7 to 10 years", "online", "security, networking, python"),
        
        # --- MENTEES (Current Students) ---
        ("student1@aston.ac.uk", "mentee", "computer science", "0 to 1 years", "birmingham", "python, java"),
        ("student2@aston.ac.uk", "mentee", "business", "0 to 1 years", "online", "finance, excel"),
        ("student3@aston.ac.uk", "mentee", "cybersecurity", "1 to 3 years", "birmingham", "python, security"),
        
        # --- BOTH (Mid-level Alumni/Postgrads) ---
        ("alumni1@aston.ac.uk", "both", "computer science", "3 to 5 years", "flexible", "python, leadership"),
        ("alumni2@aston.ac.uk", "both", "business", "5 to 7 years", "flexible", "finance, management")
    ]
    
    # The official global password requested
    global_password = "wiuj5089"
    
    for email, role, domain, exp, loc, help_areas in official_users:
        # Create the main User account
        conn.execute("""
            INSERT INTO users (email, password, role, status, domain, experience, availability, location, is_verified)
            VALUES (?, ?, ?, 'accepted', ?, ?, 'flexible', ?, 1)
        """, (email, global_password, role, domain, exp, loc))
        
        # Get their newly generated ID
        user_id = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()[0]
        
        # Create the necessary Profiles based on their role
        if role in ["mentor", "both"]:
            conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, 'mentor')", (user_id,))
        if role in ["mentee", "both"]:
            conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, 'mentee')", (user_id,))
            
        # Fill out their Questionnaire automatically
        conn.execute("INSERT INTO questionnaires (user_id, help_areas) VALUES (?, ?)", (user_id, help_areas))

    conn.commit()
    conn.close()
    
    print(" System successfully reset!")
    print(f"Created {len(official_users)} official accounts.")
    print(f"All accounts use the password: {global_password}")

if __name__ == "__main__":
    factory_reset_and_seed()