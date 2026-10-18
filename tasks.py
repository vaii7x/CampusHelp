
from datetime import date, datetime, time, timedelta
from database import get_connection

WINDOW_START = 8 * 60
WINDOW_END = 13 * 60
PICKUP_DURATION = 15
SHORT_BREAK = 10


# -------------------- TIME HELPERS --------------------

def read_date(prompt):
    while True:
        try:
            selected = datetime.strptime(
                input(prompt).strip(), "%Y-%m-%d"
            ).date()

            if selected < date.today():
                print("Please enter today or a future date.")
                continue

            return selected
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.")


def to_minutes(value):
    if isinstance(value, timedelta):
        return int(value.total_seconds() // 60) % 1440

    if isinstance(value, time):
        return value.hour * 60 + value.minute

    if isinstance(value, str):
        parts = value.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    raise ValueError(f"Unsupported time: {value!r}")


def format_time(minutes):
    hour = minutes // 60
    minute = minutes % 60
    suffix = "AM" if hour < 12 else "PM"
    display_hour = hour % 12 or 12
    return f"{display_hour}:{minute:02d} {suffix}"


# -------------------- AVAILABILITY --------------------

def get_students(cursor):
    cursor.execute(
        "SELECT reg_no, name FROM students ORDER BY reg_no"
    )
    return cursor.fetchall()


def get_labs_for_date(cursor, selected_date):
    # Python: Monday=0, Sunday=6.
    # Database: Sunday=1, Monday=2, ..., Saturday=7.
    if selected_date.weekday() == 6:
        return {}

    day_number = selected_date.weekday() + 2

    cursor.execute("""
        SELECT t.reg_no, c.start_time, c.end_time
        FROM classes c
        JOIN timetables t ON t.timetable_id = c.timetable_id
        WHERE c.day_of_week = %s
        ORDER BY t.reg_no, c.start_time
    """, (day_number,))

    labs = {}

    for reg_no, start, end in cursor.fetchall():
        labs.setdefault(reg_no, []).append(
            (to_minutes(start), to_minutes(end))
        )

    return labs


def get_free_intervals(student_labs):
    clipped = []

    for start, end in student_labs:
        start = max(start, WINDOW_START)
        end = min(end, WINDOW_END)

        if start < end:
            clipped.append((start, end))

    clipped.sort()
    merged = []

    for start, end in clipped:
        if not merged:
            merged.append([start, end])
        elif start - merged[-1][1] <= SHORT_BREAK:
            # A gap of 10 minutes or less is unusable.
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    free = []
    current = WINDOW_START

    for start, end in merged:
        if start > current:
            free.append((current, start))
        current = max(current, end)

    if current < WINDOW_END:
        free.append((current, WINDOW_END))

    return free


def get_eligible_students(cursor, selected_date):
    students = get_students(cursor)
    labs = get_labs_for_date(cursor, selected_date)
    results = []

    for reg_no, name in students:
        intervals = get_free_intervals(labs.get(reg_no, []))
        usable = [
            (start, end)
            for start, end in intervals
            if end - start >= PICKUP_DURATION
        ]

        results.append({
            "reg_no": reg_no,
            "name": name,
            "free_intervals": intervals,
            "usable_intervals": usable,
            "eligible": bool(usable)
        })

    return results


def display_availability(results, selected_date):
    print(f"\nAvailability for {selected_date}")
    print("Pickup window: 08:00 AM - 01:00 PM")
    print("Required continuous free time: 15 minutes")
    print("=" * 55)

    for student in results:
        print(
            f"\n{student['name']} ({student['reg_no']})"
        )

        if not student["free_intervals"]:
            print("  No free intervals.")
        else:
            for start, end in student["free_intervals"]:
                duration = end - start
                status = (
                    "Pickup possible"
                    if duration >= PICKUP_DURATION
                    else "Too short"
                )

                print(
                    f"  {format_time(start)} - "
                    f"{format_time(end)} "
                    f"({duration} min) - {status}"
                )

        print(
            "  Overall: " +
            ("ELIGIBLE" if student["eligible"]
             else "NOT ELIGIBLE")
        )


def find_eligible_students():
    selected_date = read_date("Pickup date (YYYY-MM-DD): ")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        results = get_eligible_students(cursor, selected_date)
        display_availability(results, selected_date)
    except Exception as error:
        print("Could not check availability:", error)
    finally:
        cursor.close()
        conn.close()


# -------------------- REQUEST A PICKUP --------------------

def request_pickup():
    print("\n--- Request an Amazon Pickup ---")

    reg_no = input("Your registration number: ").strip()
    selected_date = read_date("Pickup date (YYYY-MM-DD): ")
    location = input("Pickup location: ").strip()
    description = input("Description: ").strip()

    if not location or not description:
        print("Location and description cannot be empty.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT reg_no FROM students WHERE reg_no = %s",
            (reg_no,)
        )

        if cursor.fetchone() is None:
            print("Student not found.")
            return

        cursor.execute("""
            INSERT INTO tasks
                (created_by, title, description, location,
                 task_date, status)
            VALUES (%s, %s, %s, %s, %s, 'open')
        """, (
            reg_no,
            "Amazon Parcel Pickup",
            description,
            location,
            selected_date
        ))

        task_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO task_requests (task_id, reg_no, status)
            VALUES (%s, %s, 'pending')
        """, (task_id, reg_no))

        conn.commit()
        print(f"Pickup request created. Request ID: {task_id}")

    except Exception as error:
        conn.rollback()
        print("Could not create request:", error)
    finally:
        cursor.close()
        conn.close()


# -------------------- VIEW REQUESTS --------------------

def view_requests():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT t.task_id, t.created_by, s.name,
                   t.task_date, t.location, t.description, t.status
            FROM tasks t
            JOIN students s ON s.reg_no = t.created_by
            ORDER BY t.task_date, t.task_id
        """)

        rows = cursor.fetchall()

        if not rows:
            print("No pickup requests found.")
            return

        for row in rows:
            task_id, reg_no, name, task_date, location, description, status = row

            print("\n" + "-" * 45)
            print(f"Request ID: {task_id}")
            print(f"Requester: {name} ({reg_no})")
            print(f"Date: {task_date}")
            print(f"Location: {location}")
            print(f"Description: {description}")
            print(f"Status: {status}")

    except Exception as error:
        print("Could not retrieve requests:", error)
    finally:
        cursor.close()
        conn.close()


# -------------------- ASSIGN A PICKUP --------------------

def assign_pickup():
    try:
        task_id = int(input("Pickup request ID: ").strip())
        if task_id <= 0:
            print("Request ID must be positive.")
            return
    except ValueError:
        print("Enter a valid request ID.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT task_id, task_date, status
            FROM tasks
            WHERE task_id = %s
        """, (task_id,))

        task = cursor.fetchone()

        if task is None:
            print("Request not found.")
            return

        _, selected_date, status = task

        if status != "open":
            print(f"Request is not open. Current status: {status}")
            return

        if isinstance(selected_date, datetime):
            selected_date = selected_date.date()

        results = get_eligible_students(cursor, selected_date)
        display_availability(results, selected_date)

        eligible_ids = {
            student["reg_no"]
            for student in results
            if student["eligible"]
        }

        if not eligible_ids:
            print("No eligible students found.")
            return

        reg_no = input(
            "\nRegistration number to assign: "
        ).strip()

        if reg_no not in eligible_ids:
            print("Student is not eligible for this date.")
            return

        cursor.execute("""
            SELECT assignment_id
            FROM assignments
            WHERE task_id = %s
        """, (task_id,))

        if cursor.fetchone():
            print("This task already has an assignment.")
            return

        cursor.execute("""
            INSERT INTO assignments (task_id, reg_no, status)
            VALUES (%s, %s, 'assigned')
        """, (task_id, reg_no))

        cursor.execute("""
            UPDATE tasks
            SET status = 'assigned'
            WHERE task_id = %s
        """, (task_id,))

        conn.commit()
        print(f"Task {task_id} assigned to {reg_no}.")

    except Exception as error:
        conn.rollback()
        print("Could not assign pickup:", error)
    finally:
        cursor.close()
        conn.close()


# -------------------- VIEW ASSIGNED TASKS --------------------

def view_assigned_tasks():
    reg_no = input(
        "Enter student registration number: "
    ).strip()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT name FROM students WHERE reg_no = %s",
            (reg_no,)
        )
        student = cursor.fetchone()

        if student is None:
            print("Student not found.")
            return

        cursor.execute("""
            SELECT a.assignment_id, a.task_id, t.title,
                   t.description, t.location, t.task_date,
                   a.status, a.assigned_at
            FROM assignments a
            JOIN tasks t ON t.task_id = a.task_id
            WHERE a.reg_no = %s
            ORDER BY t.task_date, a.assignment_id
        """, (reg_no,))

        rows = cursor.fetchall()

        print(f"\nAssigned tasks for {student[0]} ({reg_no})")

        if not rows:
            print("No tasks assigned to this student.")
            return

        for row in rows:
            assignment_id, task_id, title, description, location, task_date, status, assigned_at = row

            print("\n" + "-" * 45)
            print(f"Assignment ID: {assignment_id}")
            print(f"Task ID: {task_id}")
            print(f"Title: {title}")
            print(f"Description: {description}")
            print(f"Location: {location}")
            print(f"Date: {task_date}")
            print(f"Assignment status: {status}")
            print(f"Assigned at: {assigned_at}")

    except Exception as error:
        print("Could not retrieve assigned tasks:", error)
    finally:
        cursor.close()
        conn.close()


# -------------------- MAIN TASK MENU --------------------

def manage_tasks():
    while True:
        print("\n========== CAMPUSHELP ==========")
        print("1. Request an Amazon pickup")
        print("2. View pickup requests")
        print("3. Find free intervals")
        print("4. Assign a pickup")
        print("5. View tasks assigned to a student")
        print("6. Back to main menu")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            request_pickup()
        elif choice == "2":
            view_requests()
        elif choice == "3":
            find_eligible_students()
        elif choice == "4":
            assign_pickup()
        elif choice == "5":
            view_assigned_tasks()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Try again.")
