import sqlite3

def seed_database():
    conn = sqlite3.connect("database.db")
    
    print("Cleaning up old test data...")
    # Get all test user IDs to cascade deletes safely
    test_users = conn.execute("SELECT id FROM users WHERE email LIKE '%@test.com'").fetchall()
    test_ids = [str(u[0]) for u in test_users]
    
    if test_ids:
        id_list = ",".join(test_ids)
        conn.execute(f"DELETE FROM profiles WHERE user_id IN ({id_list})")
        conn.execute(f"DELETE FROM questionnaires WHERE user_id IN ({id_list})")
        conn.execute(f"DELETE FROM matches WHERE mentor_id IN ({id_list}) OR mentee_id IN ({id_list})")
        conn.execute(f"DELETE FROM declined_pairs WHERE mentor_id IN ({id_list}) OR mentee_id IN ({id_list})")
    
    conn.execute("DELETE FROM users WHERE email LIKE '%@test.com'")

    print(" Injecting new complex ecosystem...")
    
    # FORMAT: (email, role, domain, experience)
    # Note: We set availability to 'flexible' and location to 'online' to focus purely on the algorithm's core logic.
    users_data = [
        # --- THE COMPUTER SCIENCE TREE ---
        ("1_senior_cs@test.com", "mentor", "cybersecurity", "10+ years"),   # Top level
        ("2_mid_cs@test.com",    "both",   "computer science", "5 to 7 years"),# Middle level
        ("3_junior_cs@test.com", "mentee", "computer science", "1 to 3 years"),# Bottom level
        
        # --- THE BUSINESS TREE ---
        ("4_senior_biz@test.com", "mentor", "business", "7 to 10 years"), # Top level
        ("5_mid_biz@test.com",    "both",   "accounting", "3 to 5 years"),  # Middle level
        ("6_junior_biz@test.com", "mentee", "business", "0 to 1 years"),  # Bottom level
    ]

    for email, role, domain, exp in users_data:
        conn.execute("""
            INSERT INTO users (email, password, role, status, domain, experience, availability, location, is_verified)
            VALUES (?, 'password', ?, 'accepted', ?, ?, 'flexible', 'online', 1)
        """, (email, role, domain, exp))

    # Fetch newly created users
    new_users = conn.execute("SELECT id, email, role FROM users WHERE email LIKE '%@test.com'").fetchall()
    
    # Map exact skills so the algorithm finds overlaps
    help_areas_map = {
        "1_senior_cs@test.com": "python, architecture, security",
        "2_mid_cs@test.com":    "python, leadership",
        "3_junior_cs@test.com": "python, java",
        
        "4_senior_biz@test.com": "finance, management, strategy",
        "5_mid_biz@test.com":    "finance, leadership",
        "6_junior_biz@test.com": "finance, excel"
    }

    for user in new_users:
        user_id, email, role = user
        
        #  If role is 'both', they need TWO profiles in the database
        if role in ["mentor", "both"]:
            conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, 'mentor')", (user_id,))
        if role in ["mentee", "both"]:
            conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, 'mentee')", (user_id,))
            
        # Create Questionnaire
        help_area = help_areas_map.get(email, "general")
        conn.execute("INSERT INTO questionnaires (user_id, help_areas) VALUES (?, ?)", (user_id, help_area))

    conn.commit()
    conn.close()
    print("Successfully injected! 2 Mentors, 2 Mentees, and 2 'Both' roles.")

if __name__ == "__main__":
    seed_database()