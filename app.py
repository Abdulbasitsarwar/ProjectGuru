from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime, timedelta, date

from flask_mail import Mail, Message
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"


# =====================================================
# 🔐 EMAIL CONFIGURATION (STEP 2 GOES HERE)
# =====================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "astonmentoringscheme@gmail.com"
app.config["MAIL_PASSWORD"] = "spjgtubburabshaz"

mail = Mail(app)

# =====================================================

# ---------------- ADMIN CREDENTIALS ----------------

ADMIN_EMAIL = "admin@guru.com"
ADMIN_PASSWORD = "wiuj5089"

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        # 🔐 Check against backend credentials
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin")

        return "Invalid admin credentials"

    return render_template("admin_login.html")

@app.route("/admin_logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect("/admin_login")

# ============================================================
# ---------------- DATABASE CONNECTION ----------------
# This function connects Flask to the SQLite database
# Every time we need database access we call get_db()
# ============================================================

def get_db():

    conn = sqlite3.connect("database.db", timeout=30)

    # This allows us to access columns like:
    # user["email"] instead of user[0]
    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# ---------------- NOTIFICATION HELPER ----------------
# This function saves a notification for a user.
#
# We can call it anywhere in the system.
#
# Example usage:
# create_notification(user_id,
#                     "You received a new message",
#                     "/chat/5")
#
# user_id  → who receives the notification
# message  → what the notification says
# link     → where clicking the notification sends the user
# ============================================================

def create_notification(conn, user_id, message, link=None):

    conn.execute("""
        INSERT INTO notifications (user_id, message, link)
        VALUES (?, ?, ?)
    """, (user_id, message, link))



# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        role = request.form.get("role")

        if password != confirm:
            return "Passwords do not match"

        conn = get_db()

        existing = conn.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing:
            conn.close()
            return "Email already registered"

        import random

        verification_code = str(random.randint(100000, 999999))

        # ✅ SEND EMAIL
        msg = Message(
            subject="Project Guru Verification Code",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )

        msg.body = f"""
Welcome to Project Guru!

Your verification code is:

{verification_code}

Enter this code to verify your account.
"""

        mail.send(msg)

        print("Verification code:", verification_code)

        conn.execute("""
            INSERT INTO users
            (email, password, role, status, verification_code)
            VALUES (?, ?, ?, 'incomplete', ?)
        """, (email, password, role, verification_code))

        user = conn.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        ).fetchone()

        user_id = user["id"]

        # 🔥 CREATE PROFILES BASED ON ROLE
        if role == "mentor":
            conn.execute(
                "INSERT INTO profiles (user_id, role) VALUES (?, 'mentor')",
                (user_id,)
            )

        elif role == "mentee":
            conn.execute(
                "INSERT INTO profiles (user_id, role) VALUES (?, 'mentee')",
                (user_id,)
            )

        elif role == "both":
            conn.execute(
                "INSERT INTO profiles (user_id, role) VALUES (?, 'mentor')",
                (user_id,)
            )
            conn.execute(
                "INSERT INTO profiles (user_id, role) VALUES (?, 'mentee')",
                (user_id,)
            )

        conn.commit()

        # 🔥 LOAD FIRST PROFILE IMMEDIATELY
        profile = conn.execute("""
            SELECT * FROM profiles
            WHERE user_id=?
            ORDER BY id
            LIMIT 1
        """, (user_id,)).fetchone()

        # 🔥 SET SESSION
        session["user_id"] = user_id
        session["profile_id"] = profile["id"]
        session["active_role"] = profile["role"]

        conn.close()

        return redirect("/questionnaire")

    return render_template("signup.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")

        conn = get_db()

        user = conn.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if not user:
            conn.close()
            return "Email not found"

        # 🔢 Generate reset code
        reset_code = str(random.randint(100000, 999999))

        conn.execute(
            "UPDATE users SET reset_code=? WHERE id=?",
            (reset_code, user["id"])
        )
        conn.commit()
        conn.close()

        # 📧 Send email
        msg = Message(
            subject="Project Guru Password Reset Code",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )

        msg.body = f"""
Your password reset code is:

{reset_code}

Enter this code to reset your password.
"""

        mail.send(msg)

        session["reset_email"] = email

        return redirect("/reset_password")

    return render_template("forgot_password.html")

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():

    if "reset_email" not in session:
        return redirect("/login")

    if request.method == "POST":

        code = request.form.get("code")
        new_password = request.form.get("password")

        conn = get_db()

        user = conn.execute(
            "SELECT id, reset_code FROM users WHERE email=?",
            (session["reset_email"],)
        ).fetchone()

        if not user or code != user["reset_code"]:
            conn.close()
            return "Invalid reset code"

        conn.execute(
            "UPDATE users SET password=?, reset_code=NULL WHERE id=?",
            (new_password, user["id"])
        )

        conn.commit()
        conn.close()

        session.pop("reset_email")

        return redirect("/login")

    return render_template("reset_password.html")

@app.route("/verify_email", methods=["GET", "POST"])
def verify_email():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        entered_code = request.form.get("code")

        conn = get_db()

        saved = conn.execute("""
            SELECT verification_code
            FROM users
            WHERE id=?
        """, (session["user_id"],)).fetchone()

        # ✅ Correct code
        if saved and entered_code == saved["verification_code"]:

            conn.execute("""
                UPDATE users
                SET is_verified = 1
                WHERE id = ?
            """, (session["user_id"],))

            conn.commit()
            conn.close()

            return redirect("/dashboard")

        conn.close()
        return "Invalid verification code"

    return render_template("verify_email.html")

@app.route("/switch_profile/<int:profile_id>")
def switch_profile(profile_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    profile = conn.execute("""
        SELECT * FROM profiles
        WHERE id=? AND user_id=?
    """, (profile_id, session["user_id"])).fetchone()

    conn.close()

    if not profile:
        return redirect("/dashboard")

    session["profile_id"] = profile["id"]
    session["active_role"] = profile["role"]

    return redirect("/dashboard")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

        # ❌ Invalid credentials
        if not user:
            conn.close()
            return "Invalid credentials"

        # ==========================================
        # 📋 QUESTIONNAIRE GATE FIRST
        # If user signed up but did not complete form
        # ==========================================
        if user["status"] == "incomplete":
            session["user_id"] = user["id"]
            conn.close()
            return redirect("/questionnaire")

        # ==========================================
        # 🔒 EMAIL VERIFICATION GATE SECOND
        # ==========================================
        if user["is_verified"] == 0:
            session["user_id"] = user["id"]
            conn.close()
            return redirect("/verify_email")

        # ==========================================
        # ✅ NORMAL LOGIN (your original behavior)
        # ==========================================
        session["user_id"] = user["id"]

        # -------------------------------------------------
        # 🔥 ENSURE USER HAS PROFILES
        # -------------------------------------------------
        profiles = conn.execute("""
            SELECT * FROM profiles
            WHERE user_id=?
        """, (user["id"],)).fetchall()

        if not profiles:

            if user["role"] == "mentor":
                conn.execute(
                    "INSERT INTO profiles (user_id, role) VALUES (?, 'mentor')",
                    (user["id"],)
                )

            elif user["role"] == "mentee":
                conn.execute(
                    "INSERT INTO profiles (user_id, role) VALUES (?, 'mentee')",
                    (user["id"],)
                )

            elif user["role"] == "both":
                conn.execute(
                    "INSERT INTO profiles (user_id, role) VALUES (?, 'mentor')",
                    (user["id"],)
                )
                conn.execute(
                    "INSERT INTO profiles (user_id, role) VALUES (?, 'mentee')",
                    (user["id"],)
                )

            conn.commit()

            profiles = conn.execute("""
                SELECT * FROM profiles
                WHERE user_id=?
            """, (user["id"],)).fetchall()

        # -------------------------------------------------
        # 🔥 LOAD FIRST PROFILE
        # -------------------------------------------------
        first_profile = profiles[0]

        session["profile_id"] = first_profile["id"]
        session["active_role"] = first_profile["role"]

        conn.close()

        return redirect("/dashboard")

    # 🟢 GET request → show login page
    return render_template("login.html")


# ---------------- QUESTIONNAIRE ----------------
@app.route("/questionnaire", methods=["GET", "POST"])
def questionnaire():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    user_id = session["user_id"]

    if request.method == "POST":

        level = request.form.get("level")
        experience = request.form.get("experience")
        helps = request.form.getlist("help")
        domain = request.form.get("domain")
        availability = request.form.get("availability")
        location = request.form.get("location")

        if not level or not experience or not helps or not domain or not availability or not location:
            conn.close()
            return "Please complete all fields"

        # Update user profile and set status to pending
        conn.execute("""
            UPDATE users
            SET level=?, experience=?, domain=?, availability=?, location=?, status='pending'
            WHERE id=?
        """, (level, experience, domain, availability, location, user_id))

        # Save questionnaire answers
        conn.execute("""
            INSERT INTO questionnaires (user_id, help_areas)
            VALUES (?, ?)
        """, (user_id, ", ".join(helps)))

        # ✅ PROFESSIONAL NOTIFICATION
        create_notification(
            conn,
            user_id,
            "Your application has been submitted and is currently under administrative review.",
            "/dashboard"
        )

        conn.commit()
        conn.close()

        return redirect("/verify_email")

    conn.close()
    return render_template("questionnaire.html")

# ============================================================
# --------- ACTIVE PROFILE HELPER ----------------
# Ensures user has selected a profile (mentor/mentee)
# ============================================================

def get_active_profile():

    if "profile_id" not in session:
        return None

    conn = get_db()

    profile = conn.execute("""
        SELECT * FROM profiles
        WHERE id=? AND user_id=?
    """, (session["profile_id"], session["user_id"])).fetchone()

    conn.close()

    return profile

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    # =====================================================
    # 🔥 THE FINAL STEP: TRIGGER EXPIRATION CHECK
    # This automatically clears matches that passed your 
    # minute-based limit every time a user logs in or 
    # refreshes their dashboard.
    # =====================================================
    expire_old_matches(conn) 
    conn.commit()

    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()

    if not user:
        session.clear()
        conn.close()
        return redirect("/login")

    user_id = session["user_id"]
    profile = get_active_profile()

    if not profile:
        conn.close()
        return "Please select a profile"

    role = profile["role"]

    if role == "mentor":
        matches = conn.execute("SELECT * FROM matches WHERE mentor_id=?", (user_id,)).fetchall()
    else:
        matches = conn.execute("SELECT * FROM matches WHERE mentee_id=?", (user_id,)).fetchall()

    match = next((m for m in matches if m["status"] == "final"), None)

    # =================================================
    # 📅 MEETING SYSTEM (FILTERING PAST SLOTS)
    # =================================================
    slots = []
    upcoming_meetings = []
    past_meetings = []
    now = datetime.now()

    if match:
        all_slots = conn.execute("""
            SELECT * FROM meeting_slots
            WHERE match_id=? AND status != 'unavailable'
            ORDER BY date, start_time
        """, (match["id"],)).fetchall()

        for slot in all_slots:
            slot_dt = datetime.strptime(f"{slot['date']} {slot['start_time']}", "%Y-%m-%d %H:%M")

            if slot["status"] == "available":
                if slot_dt > now:
                    slots.append(slot)
            elif slot["status"] == "booked":
                if slot_dt > now:
                    upcoming_meetings.append(slot)
                else:
                    past_meetings.append(slot)
            elif slot["status"] in ["completed", "missed"]:
                past_meetings.append(slot)

    # =================================================
    # 🔔 ROLE-AWARE RECENT ACTIVITY
    # =================================================
    if role == "mentor":
        notifications = conn.execute("""
            SELECT DISTINCT n.* FROM notifications n
            LEFT JOIN matches m ON n.link LIKE '/chat/' || m.id
            WHERE n.user_id=? AND (m.mentor_id=? OR m.id IS NULL)
            ORDER BY n.created_at DESC
        """, (user_id, user_id)).fetchall()
    else:
        notifications = conn.execute("""
            SELECT DISTINCT n.* FROM notifications n
            LEFT JOIN matches m ON n.link LIKE '/chat/' || m.id
            WHERE n.user_id=? AND (m.mentee_id=? OR m.id IS NULL)
            ORDER BY n.created_at DESC
        """, (user_id, user_id)).fetchall()

    user_profiles = conn.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,)).fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        role=role,
        user_profiles=user_profiles,
        matches=matches,
        match=match,
        slots=slots,
        upcoming_meetings=upcoming_meetings,
        past_meetings=past_meetings,
        notifications=notifications,
        current_date=date.today(),
        user_id=user_id,
    )
    
@app.route("/save_meeting_notes/<int:slot_id>", methods=["POST"])
def save_meeting_notes(slot_id):
    if "user_id" not in session:
        return redirect("/login")
    
    notes = request.form.get("notes")
    user_id = session["user_id"]
    profile = get_active_profile() # mentor or mentee
    
    conn = get_db()
    
    # Check if the user is the mentor or mentee for this specific slot
    slot = conn.execute("SELECT * FROM meeting_slots WHERE id=?", (slot_id,)).fetchone()
    match = conn.execute("SELECT * FROM matches WHERE id=?", (slot['match_id'],)).fetchone()
    
    if profile['role'] == "mentor" and match['mentor_id'] == user_id:
        conn.execute("UPDATE meeting_slots SET mentor_notes=? WHERE id=?", (notes, slot_id))
    elif profile['role'] == "mentee" and match['mentee_id'] == user_id:
        conn.execute("UPDATE meeting_slots SET mentee_notes=? WHERE id=?", (notes, slot_id))
    
    conn.commit()
    conn.close()
    return redirect("/dashboard?tab=past")

@app.route("/clear_notifications")
def clear_notifications():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    conn.execute("""
        DELETE FROM notifications
        WHERE user_id=?
    """, (session["user_id"],))

    conn.commit()
    conn.close()

    return redirect("/dashboard")




@app.route("/accept_match/<int:match_id>")
def accept_match(match_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    user_id = session["user_id"]

    match = conn.execute(
        "SELECT * FROM matches WHERE id=?",
        (match_id,)
    ).fetchone()

    if not match:
        conn.close()
        return redirect("/dashboard")

    # ---------------- RECORD USER RESPONSE ----------------
    if user_id == match["mentor_id"]:
        conn.execute(
            "UPDATE matches SET mentor_response='accepted' WHERE id=?",
            (match_id,)
        )

    elif user_id == match["mentee_id"]:
        conn.execute(
            "UPDATE matches SET mentee_response='accepted' WHERE id=?",
            (match_id,)
        )

    # ---------------- CHECK BOTH ACCEPTED ----------------
    updated = conn.execute(
        "SELECT mentor_response, mentee_response FROM matches WHERE id=?",
        (match_id,)
    ).fetchone()

    if updated["mentor_response"] == "accepted" and updated["mentee_response"] == "accepted":

        # FINALIZE MATCH
        conn.execute(
            "UPDATE matches SET status='final' WHERE id=?",
            (match_id,)
        )

        # Notify BOTH users
        create_notification(
            conn,
            match["mentor_id"],
            "Your mentoring match has been confirmed. You can now start chatting.",
            f"/chat/{match_id}"
        )

        create_notification(
            conn,
            match["mentee_id"],
            "Your mentoring match has been confirmed. You can now start chatting.",
            f"/chat/{match_id}"
        )

        # Remove other matches involving these users
        conn.execute("""
            DELETE FROM matches
            WHERE id != ?
            AND (mentor_id=? OR mentee_id=?)
        """, (match_id, match["mentor_id"], match["mentee_id"]))

    conn.commit()
    conn.close()

    # ✅ IMPORTANT FIX
    return redirect("/match")


@app.route("/decline_match/<int:match_id>")
def decline_match(match_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    selected = conn.execute("""
        SELECT mentor_id, mentee_id
        FROM matches
        WHERE id=?
    """, (match_id,)).fetchone()

    if not selected:
        conn.close()
        return redirect("/dashboard")

    mentor_id = selected["mentor_id"]
    mentee_id = selected["mentee_id"]

    # ❌ Mark match as declined
    conn.execute("""
        UPDATE matches
        SET status='declined',
            mentor_response='declined',
            mentee_response='declined'
        WHERE id=?
    """, (match_id,))

    # 🚫 Prevent these two from matching again
    conn.execute("""
        INSERT INTO declined_pairs (mentor_id, mentee_id)
        VALUES (?, ?)
    """, (mentor_id, mentee_id))

    # 🔓 Restore hidden suggestions for BOTH users
    conn.execute("""
        UPDATE matches
        SET status='pending'
        WHERE status='hidden'
        AND (mentor_id=? OR mentee_id=?)
    """, (mentor_id, mentee_id))

    # 🔔 Notify users
    create_notification(
        conn,
        mentor_id,
        "A mentoring match has been declined.",
        "/dashboard"
    )

    create_notification(
        conn,
        mentee_id,
        "A mentoring match has been declined.",
        "/dashboard"
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/cancel_accept/<int:match_id>")
def cancel_accept(match_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    user_id = session["user_id"]

    match = conn.execute(
        "SELECT * FROM matches WHERE id=?",
        (match_id,)
    ).fetchone()

    if not match:
        conn.close()
        return redirect("/dashboard")

    # 👤 If mentor cancels acceptance
    if user_id == match["mentor_id"]:
        conn.execute(
            "UPDATE matches SET mentor_response='pending' WHERE id=?",
            (match_id,)
        )

    # 👤 If mentee cancels acceptance
    elif user_id == match["mentee_id"]:
        conn.execute(
            "UPDATE matches SET mentee_response='pending' WHERE id=?",
            (match_id,)
        )

    conn.commit()
    conn.close()

    return redirect("/match")
# ---------------- USER PROFILE ----------------
@app.route("/user_profile/<int:user_id>")
def user_profile(user_id):
    conn = get_db()

    user = conn.execute("""
        SELECT u.*, q.help_areas
        FROM users u
        LEFT JOIN questionnaires q ON u.id = q.user_id
        WHERE u.id=?
    """, (user_id,)).fetchone()

    conn.close()

    return render_template("user_profile.html", user=user)

# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin():

    # 🔐 Block access if not logged in
    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    conn = get_db()

    # =====================================================
    # 🔥 THE FINAL STEP: TRIGGER EXPIRATION CHECK
    # This runs every time you refresh the admin page
    # =====================================================
    expire_old_matches(conn)
    conn.commit()

    # =====================================================
    # 🔎 USER SEARCH / FILTER
    # =====================================================
    search = request.args.get("search", "").strip()

    if search:
        users = conn.execute("""
            SELECT u.*, 
                   COALESCE(q.help_areas, 'Not filled') AS help_areas
            FROM users u
            LEFT JOIN questionnaires q ON u.id = q.user_id
            WHERE
                u.email LIKE ?
                OR u.id LIKE ?
                OR u.status LIKE ?
                OR u.is_verified LIKE ?
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
    else:
        users = conn.execute("""
            SELECT u.*,
                   COALESCE(q.help_areas, 'Not filled') AS help_areas
            FROM users u
            LEFT JOIN questionnaires q ON u.id = q.user_id
        """).fetchall()

    # =====================================================
    # 🔎 MATCH SEARCH / FILTER
    # =====================================================
    match_search = request.args.get("match_search", "").strip()

    if match_search:
        matches = conn.execute("""
            SELECT m.*,
                   u1.email AS mentor_email,
                   u2.email AS mentee_email
            FROM matches m
            JOIN users u1 ON m.mentor_id = u1.id
            JOIN users u2 ON m.mentee_id = u2.id
            WHERE u1.email LIKE ? OR u2.email LIKE ?
            ORDER BY
                CASE WHEN m.status = 'final' THEN 0 
                     WHEN m.status = 'approved' THEN 1 
                     ELSE 2 END,
                m.created_at DESC
        """, (f"%{match_search}%", f"%{match_search}%")).fetchall()
    else:
        matches = conn.execute("""
            SELECT m.*,
                   u1.email AS mentor_email,
                   u2.email AS mentee_email
            FROM matches m
            JOIN users u1 ON m.mentor_id = u1.id
            JOIN users u2 ON m.mentee_id = u2.id
            ORDER BY
                CASE WHEN m.status = 'final' THEN 0 
                     WHEN m.status = 'approved' THEN 1 
                     ELSE 2 END,
                m.created_at DESC
        """).fetchall()

    # =====================================================
    # 📊 STATS & SETTINGS
    # =====================================================
    # Get current expiry limit to show in the UI
    expiry_setting = conn.execute("SELECT value FROM settings WHERE key='match_expiry_hours'").fetchone()
    current_expiry = expiry_setting["value"] if expiry_setting else "48"

    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    pending_users = conn.execute("SELECT COUNT(*) FROM users WHERE status='pending'").fetchone()[0]
    approved_users = conn.execute("SELECT COUNT(*) FROM users WHERE status='accepted'").fetchone()[0]
    total_matches = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    final_matches = conn.execute("SELECT COUNT(*) FROM matches WHERE status='final'").fetchone()[0]

    success_rate = 0
    if total_matches > 0:
        success_rate = round((final_matches / total_matches) * 100, 2)

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        matches=matches,
        total_users=total_users,
        pending_users=pending_users,
        approved_users=approved_users,
        success_rate=success_rate,
        search=search,
        match_search=match_search,
        current_expiry=current_expiry  # Pass this to your template
    )

@app.route("/approve_user/<int:user_id>")
def approve_user(user_id):

    conn = get_db()

    # Approve user
    conn.execute(
        "UPDATE users SET status='accepted' WHERE id=?",
        (user_id,)
    )

    # ✅ PROFESSIONAL NOTIFICATION
    create_notification(
        conn,
        user_id,
        "Your application has been approved. You can now access the mentoring system.",
        "/dashboard"
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# ---------------- REMOVE USER (ADMIN) ----------------
@app.route("/remove_user/<int:user_id>")
def remove_user(user_id):

    conn = get_db()

    # --------------------------------------------------
    # 1️⃣ Find any matches involving this user
    # --------------------------------------------------
    matches = conn.execute("""
        SELECT id, mentor_id, mentee_id
        FROM matches
        WHERE mentor_id=? OR mentee_id=?
    """, (user_id, user_id)).fetchall()

    # --------------------------------------------------
    # 2️⃣ Notify the OTHER user + prevent re-matching
    # --------------------------------------------------
    for m in matches:

        other_user = m["mentee_id"] if m["mentor_id"] == user_id else m["mentor_id"]

        # Notify remaining user
        create_notification(
            conn,
            other_user,
            "Your mentoring match is no longer available.",
            "/dashboard"
        )

        # Prevent these two from being matched again
        conn.execute("""
            INSERT INTO declined_pairs (mentor_id, mentee_id)
            VALUES (?, ?)
        """, (m["mentor_id"], m["mentee_id"]))

    # --------------------------------------------------
    # 3️⃣ Delete matches involving this user
    # --------------------------------------------------
    conn.execute("""
        DELETE FROM matches
        WHERE mentor_id=? OR mentee_id=?
    """, (user_id, user_id))

    # --------------------------------------------------
    # 4️⃣ Delete questionnaire
    # --------------------------------------------------
    conn.execute("""
        DELETE FROM questionnaires
        WHERE user_id=?
    """, (user_id,))

    # --------------------------------------------------
    # 5️⃣ Delete user account
    # --------------------------------------------------
    conn.execute("""
        DELETE FROM users
        WHERE id=?
    """, (user_id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------------- SCORING FUNCTION ----------------
def calculate_score(mentor, mentee, conn):
    score = 0
    reasons = []

    # 1. HELP AREAS (Mandatory Overlap)
    mentor_data = conn.execute("SELECT help_areas FROM questionnaires WHERE user_id=?", (mentor["id"],)).fetchone()
    mentee_data = conn.execute("SELECT help_areas FROM questionnaires WHERE user_id=?", (mentee["id"],)).fetchone()

    if not mentor_data or not mentee_data:
        return 0, "Missing questionnaire"

    m_set = set(mentor_data["help_areas"].lower().split(", "))
    e_set = set(mentee_data["help_areas"].lower().split(", "))
    common = m_set & e_set

    if not common:
        return 0, "No shared support areas"
    
    score += (len(common) * 2) 
    reasons.append(f"Shared: {', '.join(common)}")

    # 2. DOMAIN CHECK (Flexible Business/Computer Science Groups)
    groups = [{"business", "accounting"}, {"computer science", "cybersecurity"}]
    m_dom = mentor["domain"].lower()
    e_dom = mentee["domain"].lower()
    
    match_group = False
    for g in groups:
        if m_dom in g and e_dom in g:
            match_group = True
    
    if not match_group and m_dom != e_dom:
        return 0, f"Domain mismatch ({m_dom} vs {e_dom})"
    
    score += 2 if m_dom == e_dom else 1
    reasons.append("Compatible Domain")

    # 3. EXPERIENCE CHECK (Mentor must be >= Mentee)
    exp_map = {"0 to 1 years": 1, "1 to 3 years": 2, "3 to 5 years": 3, "5 to 7 years": 4, "7 to 10 years": 5, "10+ years": 6}
    m_exp = exp_map.get(mentor["experience"].lower(), 0)
    e_exp = exp_map.get(mentee["experience"].lower(), 0)

    if m_exp < e_exp:
        return 0, "Mentor less experienced"
    
    score += (m_exp - e_exp) + 1
    reasons.append("Experience Valid")

    # 4. AVAILABILITY & LOCATION
    if mentor["availability"] == mentee["availability"] or mentor["availability"] == "both":
        score += 1
    if mentor["location"] == mentee["location"] or mentor["location"] == "flexible":
        score += 1

    return min(score, 10), ", ".join(reasons)

# ---------------- GENERATE MATCHES ----------------
@app.route("/generate_matches")
def generate_matches():
    conn = get_db()
    
    # 1. Clean up stale matches before starting
    expire_old_matches(conn)
    conn.commit()

    # 2. Identify "Busy" Users (Those already in an active/confirmed match)
    busy_users = conn.execute("""
        SELECT mentor_id AS uid FROM matches
        WHERE status IN ('approved', 'final')
        UNION
        SELECT mentee_id FROM matches
        WHERE status IN ('approved', 'final')
    """).fetchall()

    busy_ids = {u["uid"] for u in busy_users}

    # 3. Fetch Mentors (Role 'mentor' or 'both')
    mentors = conn.execute("""
        SELECT * FROM users
        WHERE status IN ('accepted', 'active')
        AND role IN ('mentor', 'both')
    """).fetchall()

    # 4. Fetch Mentees (Role 'mentee' or 'both')
    mentees = conn.execute("""
        SELECT * FROM users
        WHERE status IN ('accepted', 'active')
        AND role IN ('mentee', 'both')
    """).fetchall()

    for mentor in mentors:
        for mentee in mentees:
            # ❌ RULE: Cannot match with yourself
            if mentor["id"] == mentee["id"]:
                continue

            # ❌ RULE: Skip users already locked in another match
            if mentor["id"] in busy_ids or mentee["id"] in busy_ids:
                continue

            # ❌ RULE: Never re-match a pair that was previously declined or expired
            declined = conn.execute("""
                SELECT 1 FROM declined_pairs
                WHERE mentor_id=? AND mentee_id=?
            """, (mentor["id"], mentee["id"])).fetchone()

            if declined:
                continue

            # ❌ RULE: Skip if a suggestion already exists in the system
            existing = conn.execute("""
                SELECT 1 FROM matches
                WHERE mentor_id=? AND mentee_id=?
            """, (mentor["id"], mentee["id"])).fetchone()

            if existing:
                continue

            # 5. Calculate compatibility
            score, reason = calculate_score(mentor, mentee, conn)

            # 6. Lower threshold to ensure your current test users match
            if score < 3:
                continue

            # 7. Create the Suggestion (Admin must approve this next)
            conn.execute("""
                INSERT OR IGNORE INTO matches
                (mentor_id, mentee_id, score, reason,
                 status, mentor_response, mentee_response)
                VALUES (?, ?, ?, ?, 'pending', 'pending', 'pending')
            """, (mentor["id"], mentee["id"], score, reason))

    conn.commit()
    conn.close()
    return redirect("/admin")


# ---------------- APPROVE MATCH (ADMIN) ----------------
@app.route("/approve_match/<int:match_id>")
def approve_match(match_id):
    conn = get_db()

    selected = conn.execute("""
        SELECT mentor_id, mentee_id
        FROM matches
        WHERE id=?
    """, (match_id,)).fetchone()

    if not selected:
        conn.close()
        return redirect("/admin")

    m_id = selected["mentor_id"]
    e_id = selected["mentee_id"]

    # 1. Update this match to 'approved' and start the clock
    conn.execute("""
        UPDATE matches
        SET status='approved',
            created_at=datetime('now')
        WHERE id=?
    """, (match_id,))

    # 2. Hide all other 'pending' suggestions for these two users
    # This prevents them from seeing other options while one is under review
    conn.execute("""
        UPDATE matches
        SET status='hidden'
        WHERE id != ?
        AND (mentor_id=? OR mentee_id=?)
        AND status='pending'
    """, (match_id, m_id, e_id))

    # 3. Notify both users to go to their /match page
    create_notification(conn, m_id, "Admin has approved a match for you. Please Accept or Decline.", "/match")
    create_notification(conn, e_id, "Admin has approved a match for you. Please Accept or Decline.", "/match")

    conn.commit()
    conn.close()
    return redirect("/admin")


# ---------------- REMOVE MATCH (ADMIN) ----------------
@app.route("/remove_match/<int:match_id>")
def remove_match(match_id):
    conn = get_db()
    # Simply deletes the pending suggestion from the admin list
    conn.execute("DELETE FROM matches WHERE id=?", (match_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ---------------- MY MATCH PAGE ----------------
@app.route("/match")
def my_match():
    if "user_id" not in session:
        return redirect("/login")

    # 🔥 Get ACTIVE PROFILE (mentor or mentee)
    profile = get_active_profile()

    if not profile:
        return redirect("/dashboard")

    role = profile["role"]   # mentor OR mentee
    conn = get_db()
    user_id = session["user_id"]

    # ====================================================
    # 🔥 GET MATCH BASED ON ACTIVE ROLE ONLY
    # ====================================================
    if role == "mentor":
        match = conn.execute("""
            SELECT * FROM matches
            WHERE mentor_id=? AND status IN ('approved', 'final')
            ORDER BY id DESC
        """, (user_id,)).fetchone()
    else:  # mentee
        match = conn.execute("""
            SELECT * FROM matches
            WHERE mentee_id=? AND status IN ('approved', 'final')
            ORDER BY id DESC
        """, (user_id,)).fetchone()

    mentor = None
    mentee = None
    mentor_q = None
    mentee_q = None

    if match:
        # Fetch User Account Details
        mentor = conn.execute("SELECT * FROM users WHERE id=?", (match["mentor_id"],)).fetchone()
        mentee = conn.execute("SELECT * FROM users WHERE id=?", (match["mentee_id"],)).fetchone()
        
        # Fetch Questionnaire Data (to show help areas/expertise)
        mentor_q = conn.execute("SELECT * FROM questionnaires WHERE user_id=?", (match["mentor_id"],)).fetchone()
        mentee_q = conn.execute("SELECT * FROM questionnaires WHERE user_id=?", (match["mentee_id"],)).fetchone()

    # ====================================================
    # 🔥 FINAL MATCHES (for navbar chat link)
    # ====================================================
    matches = conn.execute("""
        SELECT * FROM matches 
        WHERE (mentor_id=? OR mentee_id=?) AND status='final'
    """, (user_id, user_id)).fetchall()

    conn.close()

    return render_template(
        "match.html",
        match=match,
        mentor=mentor,
        mentee=mentee,
        mentor_q=mentor_q,
        mentee_q=mentee_q,
        matches=matches,
        role=role,
        user_id=user_id
    )

# ---------------- MATCH DETAILS ----------------
@app.route("/match_details/<int:match_id>")
def match_details(match_id):
    conn = get_db()

    # Joined query to get emails and details in one go
    match = conn.execute("""
        SELECT m.*, 
               u1.email AS mentor_email, u1.domain AS mentor_domain, u1.experience AS mentor_exp,
               u2.email AS mentee_email, u2.domain AS mentee_domain, u2.level AS mentee_level,
               q1.help_areas AS mentor_help, q2.help_areas AS mentee_help
        FROM matches m
        JOIN users u1 ON m.mentor_id = u1.id
        JOIN users u2 ON m.mentee_id = u2.id
        LEFT JOIN questionnaires q1 ON m.mentor_id = q1.user_id
        LEFT JOIN questionnaires q2 ON m.mentee_id = q2.user_id
        WHERE m.id=?
    """, (match_id,)).fetchone()

    conn.close()
    return render_template("match_details.html", match=match)

# ---------------- CHAT HOME ----------------
@app.route("/chat")
def chat_home():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    user_id = session["user_id"]

    # 🔥 Get ACTIVE PROFILE (mentor or mentee)
    profile = get_active_profile()

    if not profile:
        conn.close()
        return redirect("/dashboard")

    role = profile["role"]

    # 🔎 Find FINAL match for this role
    if role == "mentor":
        match = conn.execute("""
            SELECT id FROM matches
            WHERE mentor_id=? AND status='final'
        """, (user_id,)).fetchone()

    else:
        match = conn.execute("""
            SELECT id FROM matches
            WHERE mentee_id=? AND status='final'
        """, (user_id,)).fetchone()

    conn.close()

    # ===============================
    # ✔ If match exists → open chat
    # ===============================
    if match:
        return redirect(f"/chat/{match['id']}")

    # ===============================
    # ❌ If NO match → show message
    # ===============================
    return render_template("no_chat.html")
# ---------------- CHAT ----------------
@app.route("/chat/<int:match_id>", methods=["GET", "POST"])
def chat(match_id):

    # 🔐 Check login
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    user_id = session["user_id"]

    # 🔍 Get match
    match = conn.execute("""
        SELECT m.*, 
               u1.email AS mentor_email,
               u2.email AS mentee_email
        FROM matches m
        JOIN users u1 ON m.mentor_id = u1.id
        JOIN users u2 ON m.mentee_id = u2.id
        WHERE m.id=? AND m.status='final'
    """, (match_id,)).fetchone()

    # ❌ Match not found
    if not match:
        conn.close()
        return "Chat not available"

    # 🔐 Ensure user belongs to this match
    if user_id != match["mentor_id"] and user_id != match["mentee_id"]:
        conn.close()
        return "Access denied"


    # ====================================================
    # SEND MESSAGE
    # ====================================================
    if request.method == "POST":

        text = request.form.get("message")

        if text and text.strip() != "":

            conn.execute("""
                INSERT INTO messages (match_id, sender_id, message)
                VALUES (?, ?, ?)
            """, (match_id, user_id, text.strip()))

            # ---------- NOTIFICATION ----------
            if user_id == match["mentor_id"]:
                receiver = match["mentee_id"]
            else:
                receiver = match["mentor_id"]

            create_notification(
                conn,
                receiver,
                "You have a new message from your match.",
                f"/chat/{match_id}"
            )

            conn.commit()

        conn.close()

        return redirect(f"/chat/{match_id}")


    # ====================================================
    # LOAD MESSAGES
    # ====================================================
    messages = conn.execute("""
        SELECT m.*, u.email
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.match_id=?
        ORDER BY m.timestamp ASC
    """, (match_id,)).fetchall()

    conn.close()




    # ================= RENDER PAGE =================
    return render_template(
        "chat.html",
        messages=messages,
        match=match,
        match_id=match_id,
        user_id=user_id,
    )
    
# ---------------- CHANGE PASSWORD ----------------
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        current = request.form.get("current_password")
        new = request.form.get("new_password")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()

        if user["password"] != current:
            conn.close()
            return "Current password incorrect"

        conn.execute(
            "UPDATE users SET password=? WHERE id=?",
            (new, session["user_id"])
        )
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("change_password.html")

# ---------------- DELETE ACCOUNT ----------------
@app.route("/delete_account")
def delete_account():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    user_id = session["user_id"]

    # Delete related matches
    conn.execute("DELETE FROM matches WHERE mentor_id=? OR mentee_id=?", (user_id, user_id))

    # Delete related questionnaire
    conn.execute("DELETE FROM questionnaires WHERE user_id=?", (user_id,))

    # Delete user
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))

    conn.commit()
    conn.close()

    session.clear()

    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
# ==============profile=======================
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    # 🔥 Get ACTIVE PROFILE (mentor or mentee)
    profile = get_active_profile()

    if not profile:
        return redirect("/dashboard")

    role = profile["role"]

    conn = get_db()

    # -------------------------------------------------
    # USER INFO (same for both roles)
    # -------------------------------------------------
    user = conn.execute("""
        SELECT u.*, q.help_areas
        FROM users u
        LEFT JOIN questionnaires q ON u.id = q.user_id
        WHERE u.id=?
    """,(session["user_id"],)).fetchone()

    # -------------------------------------------------
    # 🔥 MATCHES BASED ON ACTIVE ROLE ONLY
    # -------------------------------------------------
    if role == "mentor":
        matches = conn.execute("""
            SELECT * FROM matches
            WHERE mentor_id=?
        """,(session["user_id"],)).fetchall()

    else:  # mentee
        matches = conn.execute("""
            SELECT * FROM matches
            WHERE mentee_id=?
        """,(session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        matches=matches,
        role=role
    )
# ==============settings=======================
@app.route("/settings")
def settings():

    if "user_id" not in session:
        return redirect("/login")

    # 🔥 Get ACTIVE PROFILE (mentor or mentee)
    profile = get_active_profile()

    if not profile:
        return redirect("/dashboard")

    role = profile["role"]

    conn = get_db()

    # -------------------------------------------------
    # 🔥 LOAD MATCHES BASED ON ACTIVE ROLE ONLY
    # -------------------------------------------------
    if role == "mentor":
        matches = conn.execute("""
            SELECT * FROM matches
            WHERE mentor_id=?
        """,(session["user_id"],)).fetchall()

    else:  # mentee
        matches = conn.execute("""
            SELECT * FROM matches
            WHERE mentee_id=?
        """,(session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "settings.html",
        matches=matches,
        role=role
    )
# ============================================================
# ================= MEETING SLOT SYSTEM ======================
# ============================================================


# ================= CANCEL SLOT =================
# Mentor can cancel a booked meeting OR block an available slot
@app.route("/cancel_slot/<int:slot_id>")
def cancel_slot(slot_id):

    # -----------------------------------------
    # Ensure user is logged in
    # -----------------------------------------
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    # -----------------------------------------
    # Get slot information
    # -----------------------------------------
    slot = conn.execute("""
        SELECT *
        FROM meeting_slots
        WHERE id=?
    """, (slot_id,)).fetchone()

    # -----------------------------------------
    # Security check
    # Only the mentor who owns the slot can cancel it
    # -----------------------------------------
    if session["user_id"] != slot["mentor_id"]:
        conn.close()
        return "Not authorized"

    # -----------------------------------------
    # If slot was already booked
    # mentor cancelling means meeting cancelled
    # mentee should see this
    # -----------------------------------------
    if slot["status"] == "booked":
        new_status = "cancelled"

    # -----------------------------------------
    # If slot was NOT booked
    # mentor is simply blocking the slot
    # mentee will not see it
    # -----------------------------------------
    else:
        new_status = "unavailable"

    # -----------------------------------------
    # Update slot status
    # -----------------------------------------
    conn.execute("""
        UPDATE meeting_slots
        SET status=?
        WHERE id=?
    """, (new_status, slot_id))

    conn.commit()
    conn.close()

    # -----------------------------------------
    # Return user back to previous page
    # -----------------------------------------
    return redirect(request.referrer)

# ================= BOOK SLOT =================
@app.route("/book_slot/<int:slot_id>")
def book_slot(slot_id):

    # ---------------------------
    # Ensure user is logged in
    # ---------------------------
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    mentee_id = session["user_id"]

    # ---------------------------
    # Get slot
    # ---------------------------
    slot = conn.execute("""
        SELECT *
        FROM meeting_slots
        WHERE id=?
    """, (slot_id,)).fetchone()

    if not slot:
        conn.close()
        return redirect(request.referrer)

    # ---------------------------
    # RULE 1 — prevent booking own slot
    # ---------------------------
    if slot["mentor_id"] == mentee_id:
        conn.close()
        return "You cannot book your own slot"

    # ---------------------------
    # RULE 2 — ONLY ONE MEETING PER DAY
    # ---------------------------
    same_day_booking = conn.execute("""
        SELECT COUNT(*)
        FROM meeting_slots
        WHERE mentee_id=? 
        AND date=? 
        AND status='booked'
    """, (mentee_id, slot["date"])).fetchone()[0]

    if same_day_booking >= 1:
        conn.close()
        return "Only ONE meeting per day is allowed"

    # ---------------------------
    # Get match_id for this mentor + mentee
    # ---------------------------
    match = conn.execute("""
        SELECT id
        FROM matches
        WHERE mentor_id=? AND mentee_id=?
        AND status IN ('approved','final')
    """, (slot["mentor_id"], mentee_id)).fetchone()

    match_id = match["id"] if match else None

    # ---------------------------
    # Book the slot
    # ---------------------------
    conn.execute("""
        UPDATE meeting_slots
        SET status='booked',
            mentee_id=?,
            match_id=?
        WHERE id=?
    """, (mentee_id, match_id, slot_id))

    # ---------------------------
    # PROFESSIONAL NOTIFICATIONS
    # ---------------------------

    # Notify mentor
    create_notification(
        conn,
        slot["mentor_id"],
        f"A meeting has been scheduled on {slot['date']} at {slot['start_time']}.",
        "/dashboard?tab=upcoming"
    )

    # Notify mentee
    create_notification(
        conn,
        mentee_id,
        f"You have successfully booked a meeting on {slot['date']} at {slot['start_time']}.",
        "/dashboard?tab=upcoming"
    )

    conn.commit()
    conn.close()

    return redirect(request.referrer)

# ================= MARK MEETING ATTENDED =================
@app.route("/mark_attended/<int:slot_id>")
def mark_attended(slot_id):

    conn = get_db()

    conn.execute("""
        UPDATE meeting_slots
        SET status='completed'
        WHERE id=?
    """, (slot_id,))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/cancel_booking/<int:slot_id>")
def cancel_booking(slot_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    slot = conn.execute(
        "SELECT * FROM meeting_slots WHERE id=?",
        (slot_id,)
    ).fetchone()

    if slot["mentee_id"] != session["user_id"]:
        conn.close()
        return "Unauthorized"

    # return slot back to available
    conn.execute("""
        UPDATE meeting_slots
        SET status='available', mentee_id=NULL
        WHERE id=?
    """,(slot_id,))

    # notify mentor
    create_notification(
        conn,
        slot["mentor_id"],
        "Your match cancelled a scheduled meeting.",
        "/dashboard"
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/mentor_cancel_meeting/<int:slot_id>")
def mentor_cancel_meeting(slot_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    slot = conn.execute(
        "SELECT * FROM meeting_slots WHERE id=?",
        (slot_id,)
    ).fetchone()

    if session["user_id"] != slot["mentor_id"]:
        conn.close()
        return "Unauthorized"

    # ❌ DELETE SLOT COMPLETELY
    conn.execute(
        "DELETE FROM meeting_slots WHERE id=?",
        (slot_id,)
    )

    # 🔔 Notify mentee
    if slot["mentee_id"]:
        create_notification(
            conn,
            slot["mentee_id"],
            "Your mentor has cancelled the scheduled meeting. Please book another slot.",
            "/dashboard?tab=available"
        )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/mark_meeting/<int:slot_id>/<result>")
def mark_meeting(slot_id,result):

    conn = get_db()

    slot = conn.execute(
        "SELECT * FROM meeting_slots WHERE id=?",
        (slot_id,)
    ).fetchone()

    if session["user_id"] != slot["mentor_id"]:
        conn.close()
        return "Unauthorized"

    conn.execute("""
        UPDATE meeting_slots
        SET status=?
        WHERE id=?
    """,(result,slot_id))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ================= MARK MEETING MISSED =================
@app.route("/mark_missed/<int:slot_id>")
def mark_missed(slot_id):

    conn = get_db()

    conn.execute("""
        UPDATE meeting_slots
        SET status='missed'
        WHERE id=?
    """, (slot_id,))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ================= mentor adds availability =================
# This function allows mentor to add availability
# It automatically splits the availability into 30 minute slots


@app.route("/add_availability/<int:match_id>", methods=["POST"])
def add_availability(match_id):

    # -----------------------------------------
    # Ensure user is logged in
    # -----------------------------------------
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    mentor_id = session["user_id"]

    # -----------------------------------------
    # Get form values
    # -----------------------------------------
    date_input = request.form.get("date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    # -----------------------------------------
    # Convert date string to python date
    # -----------------------------------------
    selected_date = datetime.strptime(date_input, "%Y-%m-%d").date()

    # -----------------------------------------
    # RULE 1 — prevent mentor selecting past date
    # -----------------------------------------
    if selected_date < date.today():
        conn.close()
        return "❌ Cannot add availability for past dates"

    # -----------------------------------------
    # Convert start and end time
    # -----------------------------------------
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")

    # -----------------------------------------
    # RULE 2 — ensure end time is after start time
    # -----------------------------------------
    if end <= start:
        conn.close()
        return "❌ End time must be after start time"

    # -----------------------------------------
    # RULE 3 — prevent mentor adding past time today
    # -----------------------------------------
    now = datetime.now()

    if selected_date == now.date() and start.time() <= now.time():
        conn.close()
        return "❌ Start time must be in the future"

    # -----------------------------------------
    # Save the availability block
    # -----------------------------------------
    conn.execute("""
        INSERT INTO mentor_availability (mentor_id, date, start_time, end_time)
        VALUES (?, ?, ?, ?)
    """, (mentor_id, date_input, start_time, end_time))

    # -----------------------------------------
    # Split into 30 minute slots
    # AND prevent duplicate slots
    # -----------------------------------------
    while start < end:

        slot_end = start + timedelta(minutes=30)

        existing = conn.execute("""
            SELECT 1
            FROM meeting_slots
            WHERE mentor_id=? AND date=? AND start_time=?
        """, (
            mentor_id,
            date_input,
            start.strftime("%H:%M")
        )).fetchone()

        if not existing:

            conn.execute("""
                INSERT INTO meeting_slots
                (match_id, mentor_id, date, start_time, end_time, status)
                VALUES (?, ?, ?, ?, ?, 'available')
            """, (
                match_id,
                mentor_id,
                date_input,
                start.strftime("%H:%M"),
                slot_end.strftime("%H:%M")
            ))

        start = slot_end

    # -----------------------------------------
    # Save changes
    # -----------------------------------------
    # -----------------------------------------
    # Notify mentee that new slots are available
    # -----------------------------------------

    match = conn.execute(
        "SELECT mentor_id, mentee_id FROM matches WHERE id=?",
        (match_id,)
    ).fetchone()

    if match:
        create_notification(
            conn,
            match["mentee_id"],
            "Your mentor has added new meeting slots. Please check availability.",
            "/dashboard?tab=available"
        )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- GIVE FEEDBACK ----------------
@app.route("/give_feedback/<int:match_id>", methods=["POST"])
def give_feedback(match_id):

    # 🔐 Must be logged in
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    user_id = session["user_id"]

    # ✅ Only allow feedback on FINAL matches
    match = conn.execute(
        "SELECT * FROM matches WHERE id=? AND status='final'",
        (match_id,)
    ).fetchone()

    if not match:
        conn.close()
        return redirect("/dashboard")

    # ✅ Determine who is reviewing whom
    if user_id == match["mentor_id"]:
        to_user = match["mentee_id"]

    elif user_id == match["mentee_id"]:
        to_user = match["mentor_id"]

    else:
        # Not part of this match
        conn.close()
        return redirect("/dashboard")

    # ✅ Get form values safely
    rating = request.form.get("rating")
    comment = request.form.get("comment", "").strip()

    # Optional: ensure rating exists
    if not rating:
        conn.close()
        return redirect("/dashboard")

    # ✅ Insert feedback WITH timestamp
    conn.execute("""
        INSERT INTO feedback 
        (match_id, from_user, to_user, rating, comment, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (match_id, user_id, to_user, rating, comment))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- FEEDBACK HISTORY ----------------
@app.route("/feedback_history/<int:match_id>/<role>")
def feedback_history(match_id, role):

    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    conn = get_db()

    match = conn.execute("""
        SELECT m.*,
               u1.email AS mentor_email,
               u2.email AS mentee_email
        FROM matches m
        JOIN users u1 ON m.mentor_id = u1.id
        JOIN users u2 ON m.mentee_id = u2.id
        WHERE m.id=?
    """, (match_id,)).fetchone()

    if not match:
        conn.close()
        return redirect("/admin")

    # 👉 Show feedback WRITTEN BY mentor
    if role == "mentor":
        feedbacks = conn.execute("""
            SELECT f.*, u.email AS from_email
            FROM feedback f
            JOIN users u ON f.from_user = u.id
            WHERE f.match_id=? AND f.from_user=?
            ORDER BY f.created_at DESC
        """, (match_id, match["mentor_id"])).fetchall()

    # 👉 Show feedback WRITTEN BY mentee
    else:
        feedbacks = conn.execute("""
            SELECT f.*, u.email AS from_email
            FROM feedback f
            JOIN users u ON f.from_user = u.id
            WHERE f.match_id=? AND f.from_user=?
            ORDER BY f.created_at DESC
        """, (match_id, match["mentee_id"])).fetchall()

    conn.close()

    return render_template(
        "feedback_history.html",
        match=match,
        feedbacks=feedbacks,
        role=role
    )

@app.route("/cancel_match/<int:match_id>")
def cancel_match(match_id):

    conn = get_db()

    match = conn.execute(
        "SELECT mentor_id, mentee_id FROM matches WHERE id=?",
        (match_id,)
    ).fetchone()

    if not match:
        conn.close()
        return redirect("/admin")

    mentor_id = match["mentor_id"]
    mentee_id = match["mentee_id"]

    # Mark match as cancelled
    conn.execute("""
        UPDATE matches
        SET status='cancelled'
        WHERE id=?
    """, (match_id,))

    # Save this pair so they never match again
    conn.execute("""
        INSERT INTO declined_pairs (mentor_id, mentee_id)
        VALUES (?, ?)
    """, (mentor_id, mentee_id))

    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------------- CLEAR MEETING SLOTS (TEMP) ----------------
@app.route("/clear_slots")
def clear_slots():

    conn = get_db()

    conn.execute("DELETE FROM meeting_slots")

    conn.commit()
    conn.close()

    return "All meeting slots deleted"

def expire_old_matches(conn):
    # 1. Get the current limit from the settings table
    setting = conn.execute("""
        SELECT value FROM settings
        WHERE key='match_expiry_hours'
    """).fetchone()

    # Default to 48 if no setting is found in the database
    expiry_limit = int(setting["value"]) if setting else 48

    # 2. Find all matches approved by admin that haven't been finalized yet
    expired = conn.execute("""
        SELECT id, mentor_id, mentee_id, created_at
        FROM matches
        WHERE status='approved'
        AND created_at IS NOT NULL
    """).fetchall()

    for m in expired:
        # Convert the stored database time string into a Python time object
        created = datetime.strptime(m["created_at"], "%Y-%m-%d %H:%M:%S")

        # ⭐ TESTING MODE: Changed 'hours=expiry_limit' to 'minutes=expiry_limit'
        if datetime.now() - created > timedelta(minutes=expiry_limit):
            
            # Mark the match as expired so it disappears from the user's view
            conn.execute("UPDATE matches SET status='expired' WHERE id=?", (m["id"],))

            # Block these two users from being suggested together again
            conn.execute("""
                INSERT OR IGNORE INTO declined_pairs (mentor_id, mentee_id)
                VALUES (?, ?)
            """, (m["mentor_id"], m["mentee_id"]))

            # Unhide other pending matches for these users so they can find someone else
            conn.execute("""
                UPDATE matches SET status='pending'
                WHERE status='hidden' AND (mentor_id=? OR mentee_id=?)
            """, (m["mentor_id"], m["mentee_id"]))
            
@app.route("/update_expiry", methods=["POST"])
def update_expiry():
    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    # This pulls the number you typed into the input field
    duration = request.form.get("hours")

    if not duration:
        return "Please enter a valid number"

    conn = get_db()
    
    # This ensures the setting is UPDATED if it exists, or CREATED if it doesn't
    conn.execute("""
        INSERT OR REPLACE INTO settings (key, value)
        VALUES ('match_expiry_hours', ?)
    """, (duration,))

    conn.commit()
    conn.close()

    # Return to admin page to see the change
    return redirect("/admin")
# ------------------------------------------------
# MEETING SLOT STATUS TYPES
# ------------------------------------------------
# available   → slot is free for booking
# booked      → mentee has booked the slot
# cancelled   → mentor cancelled a booked meeting (mentee will see this)
# unavailable → mentor blocked the slot before booking (hidden from mentee)
# ------------------------------------------------

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)