import sqlite3

def seed_database():
    conn = sqlite3.connect("database.db")
    
    print("Clearing old test data...")
    # Optional: Clear out specific test emails if you run this multiple times
    conn.execute("DELETE FROM users WHERE email LIKE '%@test.com'")
    
    print("Injecting fake users...")
    
    # ==========================================
    # 1. CREATE USERS
    # ==========================================
    # We set status to 'accepted' so the matching engine picks them up
    users_data = [
        # MENTORS
        ("mentor_tech@test.com", "password", "mentor", "accepted", "computer science", "5 to 7 years", "flexible", "online"),
        ("mentor_biz@test.com", "password", "mentor", "accepted", "accounting", "10+ years", "weekends", "london"),
        ("mentor_rookie@test.com", "password", "mentor", "accepted", "computer science", "0 to 1 years", "weekdays", "birmingham"), # Low experience to test failure
        
        # MENTEES
        ("mentee_cyber@test.com", "password", "mentee", "accepted", "cybersecurity", "0 to 1 years", "weekends", "online"),
        ("mentee_finance@test.com", "password", "mentee", "accepted", "business", "1 to 3 years", "weekends", "london"),
        ("mentee_senior@test.com", "password", "mentee", "accepted", "computer science", "3 to 5 years", "weekdays", "birmingham"),
    ]

    for email, pwd, role, status, domain, exp, avail, loc in users_data:
        conn.execute("""
            INSERT INTO users (email, password, role, status, domain, experience, availability, location, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (email, pwd, role, status, domain, exp, avail, loc))

    # ==========================================
    # 2. CREATE PROFILES & QUESTIONNAIRES
    # ==========================================
    # Fetch the IDs of the users we just created
    test_users = conn.execute("SELECT id, email, role FROM users WHERE email LIKE '%@test.com'").fetchall()
    
    # Map emails to their help areas to test the overlap logic
    help_areas_map = {
        "mentor_tech@test.com": "python, web development, ai",
        "mentee_cyber@test.com": "python, networking", # Shares 'python' with tech mentor
        
        "mentor_biz@test.com": "leadership, finance, public speaking",
        "mentee_finance@test.com": "finance, excel", # Shares 'finance' with biz mentor
        
        "mentor_rookie@test.com": "python, java",
        "mentee_senior@test.com": "python, architecture" # Shares 'python', but mentee has MORE experience than mentor
    }

    for user in test_users:
        user_id = user[0]
        email = user[1]
        role = user[2]
        
        # Create Profile
        conn.execute("INSERT INTO profiles (user_id, role) VALUES (?, ?)", (user_id, role))
        
        # Create Questionnaire
        help_area = help_areas_map.get(email, "general")
        conn.execute("INSERT INTO questionnaires (user_id, help_areas) VALUES (?, ?)", (user_id, help_area))

    conn.commit()
    conn.close()
    print("✅ Successfully injected 3 Mentors and 3 Mentees!")

if __name__ == "__main__":
    seed_database() 