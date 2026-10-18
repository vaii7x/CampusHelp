
from datetime import time, timedelta
from database import get_connection

WINDOW_START = 8 * 60
WINDOW_END = 13 * 60
PICKUP_DURATION = 15
SHORT_BREAK = 10

DAYS = [
    ("Monday", 2),
    ("Tuesday", 3),
    ("Wednesday", 4),
    ("Thursday", 5),
    ("Friday", 6),
    ("Saturday", 7),
    ("Sunday", 1),
]


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


def get_free_intervals(labs):
    """
    Calculate free intervals between 08:00 and 13:00.
    Breaks of 10 minutes or less between labs are not usable.
    """
    clipped = []

    for start, end in labs:
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


def load_data(cursor):
    cursor.execute(
        "SELECT reg_no, name FROM students ORDER BY reg_no"
    )
    students = cursor.fetchall()

    cursor.execute("""
        SELECT t.reg_no, c.day_of_week,
               c.start_time, c.end_time
        FROM classes c
        JOIN timetables t
          ON t.timetable_id = c.timetable_id
        ORDER BY t.reg_no, c.day_of_week, c.start_time
    """)

    labs = {}

    for reg_no, day_number, start, end in cursor.fetchall():
        key = (reg_no, day_number)
        labs.setdefault(key, []).append(
            (to_minutes(start), to_minutes(end))
        )

    return students, labs


def show_student_day(reg_no, name, day_number, labs):
    # Sunday has no classes.
    day_labs = labs.get((reg_no, day_number), [])
    intervals = get_free_intervals(day_labs)

    print(f"\n{name} ({reg_no})")

    if intervals:
        for start, end in intervals:
            duration = end - start

            if duration >= PICKUP_DURATION:
                status = "PICKUP AVAILABLE"
            else:
                status = "Too short for pickup"

            print(
                f"  {format_time(start)} - {format_time(end)}"
                f" ({duration} min): {status}"
            )
    else:
        print("  No free intervals in the 08:00-13:00 window.")

    if any(
        end - start >= PICKUP_DURATION
        for start, end in intervals
    ):
        print("  Overall: ELIGIBLE for a 15-minute pickup")
    else:
        print("  Overall: NOT ELIGIBLE")


def check_student_availability():
    print("\n--- Check Student Availability ---")
    print("1. Show all students' free intervals")
    print("2. Check one student by registration number")

    choice = input("Choose an option: ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        students, labs = load_data(cursor)

        if not students:
            print("No registered students found.")
            return

        if choice == "1":
            for day_name, day_number in DAYS:
                print(f"\n{'=' * 12} {day_name} {'=' * 12}")

                for reg_no, name in students:
                    show_student_day(
                        reg_no, name, day_number, labs
                    )

        elif choice == "2":
            reg_no = input(
                "Enter college Reg No.: "
            ).strip()

            student = next(
                (
                    (r, n) for r, n in students
                    if r == reg_no
                ),
                None
            )

            if student is None:
                print("Student not found.")
                return

            reg_no, name = student

            print(
                f"\nAvailability for {name} ({reg_no})"
            )

            for day_name, day_number in DAYS:
                print(f"\n{day_name}:")
                show_student_day(
                    reg_no, name, day_number, labs
                )

        else:
            print("Invalid option.")

    except Exception as error:
        print("Could not check availability:", error)

    finally:
        cursor.close()
        conn.close()
