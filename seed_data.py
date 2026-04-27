import sqlite3

def seed_exact_html():
    conn = sqlite3.connect("database.db")
    
    print(" Wiping database to start fresh...")
    tables = ["users", "profiles", "questionnaires", "matches", "declined_pairs", "meeting_slots", "mentor_availability", "feedback", "notifications", "messages"]
    for t in tables:
        try: conn.execute(f"DELETE FROM {t}")
        except: pass

    print("🌱 Injecting users using EXACT HTML form values...")
    
    # Format: (email, role, level, experience, domain, availability, location)
    # Using exact strings from your <select> options
    users_data = [
        # --- TREE 1: The Perfect Match Chain ---
        ("senior_cs@test.com", "mentor", "lecturer", "10+", "computer_science", "both", "flexible"),
        ("mid_both_1@test.com", "both", "phd", "3-5", "computer_science", "both", "flexible"),
        ("junior_cs@test.com", "mentee", "undergraduate", "0-1", "computer_science", "both", "flexible"),
        
        # --- TREE 2: The Isolated "Both" Profile Test ---
        # This user is "both". We will match them with a Senior as a Mentee.
        # But we will NOT create a junior business student, so their Mentor profile will be empty!
        ("mid_both_2@test.com", "both", "postgraduate", "1-3", "business", "weekdays", "abs"),
        ("senior_biz@test.com", "mentor", "admin_staff", "7-10", "business", "weekdays", "abs"),
    ]

    for email, role, level, exp, domain, avail, loc in users_data:
        conn.execute("""
            INSERT INTO users (email, password, role, status, level, experience, domain, availability, location, is_verified)
            VALUES (?, 'password', ?, 'accepted', ?, ?, ?, ?, ?, 1)
        """, (email, role, level, exp, domain, avail, loc))

    users = conn.execute("SELECT id, email, role FROM users").fetchall()
    
    # Using exact strings from your <input type="checkbox"> options
    help_areas = {
        "senior_cs@test.com": "cv, career",
        "mid_both_1@test.com": "cv, placements",
        "junior_cs@test.com": "placements",
        
        "mid_both_2@test.com": "leadership, professional_dev",
        "senior_biz@test.com": "leadership, professional_dev"
    }

    for u_id, email, role in users:
        # Create correct profiles
        if role in ["mentor", "both"]:
            conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, 'mentor')", (u_id,))
        if role in ["mentee", "both"]:
            conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, 'mentee')", (u_id,))
            
        # Insert exact checkbox values
        conn.execute("INSERT INTO questionnaires (user_id, help_areas) VALUES (?, ?)", (u_id, help_areas[email]))

    conn.commit()
    conn.close()
    print(" System successfully loaded with EXACT HTML values!")

if __name__ == "__main__":
    seed_exact_html()