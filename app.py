import os
import hashlib
import hmac
from functools import wraps

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-key")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "CampusHelp"),
}


def db(sql, args=(), one=False, write=False):
    """Run a query against the CampusHelp database and always close resources."""
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, args)
        if write:
            connection.commit()
            return cursor.lastrowid
        rows = cursor.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        cursor.close()
        connection.close()


def verify_cli_password(password, stored_hash):
    """Verify the PBKDF2-HMAC-SHA256 format used by the existing CLI."""
    try:
        salt_hex, expected_hash = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200_000,
        ).hex()
        return hmac.compare_digest(actual_hash, expected_hash)
    except (ValueError, TypeError, AttributeError):
        return False


def verify_password(password, stored_hash):
    """Support Werkzeug hashes and the existing CLI's PBKDF2 hashes."""
    if not stored_hash:
        return False
    try:
        if check_password_hash(stored_hash, password):
            return True
    except (ValueError, TypeError):
        pass
    return verify_cli_password(password, stored_hash)


def signed_in(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("reg_no"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    return render_template("page.html", page="home")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        reg_no = request.form.get("reg_no", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip() or None
        semester_value = request.form.get("semester", "").strip()
        phone = request.form.get("phone", "").strip() or None

        if not all((reg_no, name, email, password)):
            flash("Please fill in all required fields.", "error")
            return render_template("page.html", page="register")

        if len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
            return render_template("page.html", page="register")

        try:
            semester = int(semester_value) if semester_value else None
            db(
                """
                INSERT INTO students
                    (reg_no, name, email, password_hash, department, semester, phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    reg_no,
                    name,
                    email,
                    generate_password_hash(password),
                    department,
                    semester,
                    phone,
                ),
                write=True,
            )
            flash("Account created. Sign in to continue.", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("That registration number or email may already be registered.", "error")
        except Exception as exc:
            app.logger.exception("Registration failed: %s", exc)
            flash("Registration failed. Check the VS Code terminal.", "error")

    return render_template("page.html", page="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        try:
            student = db(
                """
                SELECT reg_no, password_hash
                FROM students
                WHERE reg_no = %s OR email = %s
                """,
                (identifier, identifier.lower()),
                one=True,
            )

            if student and verify_password(password, student["password_hash"]):
                session.clear()
                session["reg_no"] = student["reg_no"]
                return redirect(url_for("dashboard"))

            flash("Incorrect registration number/email or password.", "error")
        except Exception as exc:
            app.logger.exception("Login failed: %s", exc)
            flash("Login failed. Check the VS Code terminal.", "error")

    return render_template("page.html", page="login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/dashboard")
@signed_in
def dashboard():
    student = db(
        "SELECT * FROM students WHERE reg_no = %s",
        (session["reg_no"],),
        one=True,
    )
    tasks = db(
        """
        SELECT t.*, s.name AS creator
        FROM tasks t
        JOIN students s ON s.reg_no = t.created_by
        WHERE t.status = 'open' AND t.created_by <> %s
        ORDER BY t.created_at DESC
        LIMIT 6
        """,
        (session["reg_no"],),
    )
    assigned = db(
        """
        SELECT a.status AS assignment_status, t.title, t.location
        FROM assignments a
        JOIN tasks t ON t.task_id = a.task_id
        WHERE a.reg_no = %s
        ORDER BY a.assigned_at DESC
        LIMIT 5
        """,
        (session["reg_no"],),
    )
    return render_template(
        "page.html", page="dashboard", student=student, tasks=tasks, assigned=assigned
    )


@app.route("/timetable", methods=["GET", "POST"])
@signed_in
def timetable():
    days = {
        1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday",
        5: "Thursday", 6: "Friday", 7: "Saturday",
    }

    if request.method == "POST":
        try:
            day = int(request.form["day"])
            start = request.form["start"]
            end = request.form["end"]
            subject = request.form["subject"].strip()

            if not subject or start >= end:
                flash("Enter a subject and a valid start/end time.", "error")
                return redirect(url_for("timetable"))

            timetable_row = db(
                """
                SELECT timetable_id
                FROM timetables
                WHERE reg_no = %s
                ORDER BY uploaded_at DESC
                LIMIT 1
                """,
                (session["reg_no"],),
                one=True,
            )

            if timetable_row:
                timetable_id = timetable_row["timetable_id"]
            else:
                db(
                    "INSERT INTO timetables (reg_no, status) VALUES (%s, 'active')",
                    (session["reg_no"],),
                    write=True,
                )
                new_timetable = db(
                    """
                    SELECT timetable_id FROM timetables
                    WHERE reg_no = %s
                    ORDER BY timetable_id DESC LIMIT 1
                    """,
                    (session["reg_no"],),
                    one=True,
                )
                timetable_id = new_timetable["timetable_id"]

            db(
                """
                INSERT INTO classes (timetable_id, day_of_week, start_time, end_time, subject)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (timetable_id, day, start, end, subject),
                write=True,
            )
            flash("Lab added to your timetable.", "success")
        except Exception as exc:
            app.logger.exception("Timetable save failed: %s", exc)
            flash("Could not save the lab. Check the VS Code terminal and table columns.", "error")
        return redirect(url_for("timetable"))

    classes = db(
        """
        SELECT c.*
        FROM classes c
        JOIN timetables t ON t.timetable_id = c.timetable_id
        WHERE t.reg_no = %s
        ORDER BY c.day_of_week, c.start_time
        """,
        (session["reg_no"],),
    )
    return render_template("page.html", page="timetable", classes=classes, days=days)


@app.route("/tasks", methods=["GET", "POST"])
@signed_in
def tasks_page():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip() or None
        task_date = request.form.get("task_date", "").strip() or None

        if not title or not location:
            flash("Task title and pickup location are required.", "error")
            return redirect(url_for("tasks_page"))

        try:
            db(
                """
                INSERT INTO tasks
                    (created_by, title, description, location, task_date, status)
                VALUES (%s, %s, %s, %s, %s, 'open')
                """,
                (session["reg_no"], title, description, location, task_date),
                write=True,
            )
            flash("Pickup task posted.", "success")
        except Exception as exc:
            app.logger.exception("Task creation failed: %s", exc)
            flash("Could not post the task. Check the VS Code terminal and table columns.", "error")
        return redirect(url_for("tasks_page"))

    tasks = db(
        """
        SELECT t.*, s.name AS creator
        FROM tasks t
        JOIN students s ON s.reg_no = t.created_by
        WHERE t.status = 'open' AND t.created_by <> %s
        ORDER BY t.created_at DESC
        """,
        (session["reg_no"],),
    )
    mine = db(
        """
        SELECT * FROM tasks
        WHERE created_by = %s
        ORDER BY created_at DESC
        """,
        (session["reg_no"],),
    )
    requests = db(
        """
        SELECT r.*, t.title, t.location
        FROM task_requests r
        JOIN tasks t ON t.task_id = r.task_id
        WHERE r.reg_no = %s
        ORDER BY r.requested_at DESC
        """,
        (session["reg_no"],),
    )
    return render_template(
        "page.html", page="tasks", tasks=tasks, mine=mine, requests=requests
    )


@app.route("/tasks/<int:task_id>/request", methods=["POST"])
@signed_in
def request_task(task_id):
    try:
        task = db(
            "SELECT task_id, created_by, status FROM tasks WHERE task_id = %s",
            (task_id,),
            one=True,
        )
        if not task or task["status"] != "open":
            flash("That pickup task is no longer available.", "error")
        elif task["created_by"] == session["reg_no"]:
            flash("You cannot request your own task.", "error")
        else:
            db(
                """
                INSERT INTO task_requests (task_id, requested_at, status, reg_no)
                VALUES (%s, NOW(), 'pending', %s)
                """,
                (task_id, session["reg_no"]),
                write=True,
            )
            flash("Pickup request sent.", "success")
    except mysql.connector.IntegrityError:
        flash("You may have already requested this task.", "error")
    except Exception as exc:
        app.logger.exception("Pickup request failed: %s", exc)
        flash("Could not send the request. Check the VS Code terminal.", "error")
    return redirect(url_for("tasks_page"))


@app.route("/profile", methods=["GET", "POST"])
@signed_in
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        department = request.form.get("department", "").strip() or None
        semester_value = request.form.get("semester", "").strip()
        phone = request.form.get("phone", "").strip() or None

        if not name or not email:
            flash("Name and email are required.", "error")
            return redirect(url_for("profile"))

        try:
            semester = int(semester_value) if semester_value else None
            db(
                """
                UPDATE students
                SET name = %s, email = %s, department = %s, semester = %s, phone = %s
                WHERE reg_no = %s
                """,
                (name, email, department, semester, phone, session["reg_no"]),
                write=True,
            )
            flash("Profile updated.", "success")
        except mysql.connector.IntegrityError:
            flash("That email address is already in use.", "error")
        except Exception as exc:
            app.logger.exception("Profile update failed: %s", exc)
            flash("Could not update your profile. Check the VS Code terminal.", "error")
        return redirect(url_for("profile"))

    student = db(
        "SELECT * FROM students WHERE reg_no = %s",
        (session["reg_no"],),
        one=True,
    )
    return render_template("page.html", page="profile", student=student)


if __name__ == "__main__":
    app.run(debug=True)
