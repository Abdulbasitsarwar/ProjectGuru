import sqlite3

def seed_complex_test():
    conn = sqlite3.connect("database.db")
    
    print(" Wiping database for complex test scenario...")
    tables = ["users", "profiles", "questionnaires", "matches", "declined_pairs", "meeting_slots", "feedback", "notifications", "messages"]
    for t in tables:
        conn.execute(f"DELETE FROM {t}")
        
    print(" Injecting Tayte, Nada, and the test ecosystem...")

    # ====================================================
    # THE CAST OF CHARACTERS
    # Format: (email, role, level, exp, domain, avail, loc, help_areas)
    # ====================================================
    users_data = [
        #  TAYTE ('Both' Role) - The Perfect Middleman
        # Mentors Bob (shares CV). Mentees under Turing (shares Career).
        ("tayte@aston.ac.uk", "both", "postgraduate", "3-5", "computer_science", "weekdays", "flexible", "cv, career"),
        
        #  NADA ('Both' Role) - The Asymmetric Match
        # Mentors Alice (shares Leadership). BUT has NO mentors above her 5-7 years in Business!
        ("nada@aston.ac.uk", "both", "phd", "5-7", "business", "weekends", "abs", "academic_writing, leadership"),

        #  PROF. TURING (Senior Mentor for Tayte)
        ("turing@aston.ac.uk", "mentor", "lecturer", "10+", "cyber_security", "both", "flexible", "career, research"),
        
        #  FRESHER BOB (Junior Mentee for Tayte)
        ("bob@aston.ac.uk", "mentee", "undergraduate", "0-1", "computer_science", "weekdays", "main_building", "cv, university_life"),
        
        #  JUNIOR ALICE (Junior Mentee for Nada)
        ("alice@aston.ac.uk", "mentee", "undergraduate", "0-1", "finance", "both", "flexible", "leadership, placements"),

        #  DAVE (Standard Mentor to prove normal roles work)
        ("dave@aston.ac.uk", "mentor", "research_staff", "7-10", "engineering", "weekdays", "flexible", "placements, professional_dev"),
        
        #  EVA (Standard Mentee for Dave)
        ("eva@aston.ac.uk", "mentee", "undergraduate", "1-3", "engineering", "weekdays", "flexible", "placements, cv"),
    ]

    global_password = "password"

    for email, role, level, exp, domain, avail, loc, help_areas in users_data:
        # 1. Insert User Account
        conn.execute("""
            INSERT INTO users (email, password, role, level, experience, domain, availability, location, status, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'accepted', 1)
        """, (email, global_password, role, level, exp, domain, avail, loc))
        
        user_id = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()[0]
        
        # 2. Insert Profiles (The 'Both' Magic)
        if role in ["mentor", "both"]:
            conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, 'mentor')", (user_id,))
        if role in ["mentee", "both"]:
            conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, 'mentee')", (user_id,))
            
        # 3. Insert Questionnaire Responses
        conn.execute("INSERT INTO questionnaires (user_id, help_areas) VALUES (?, ?)", (user_id, help_areas))

    conn.commit()
    conn.close()
    print(" Complex ecosystem generated successfully! All passwords are 'password'.")

if __name__ == "__main__":
    seed_complex_test()