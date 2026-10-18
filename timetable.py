
from datetime import datetime, timedelta

from database import get_connection


DAYS = [
    ("Sunday", 1),
    ("Monday", 2),
    ("Tuesday", 3),
    ("Wednesday", 4),
    ("Thursday", 5),
    ("Friday", 6),
    ("Saturday", 7),
]

LAB_DURATION_MINUTES = 100


def read_integer(prompt, minimum=0, maximum=20):
    while True:
        try:
            value = int(input(prompt).strip())
            if minimum <= value <= maximum:
                return value
        except ValueError:
            pass

        print(f"Enter a number between {minimum} and {maximum}.")


def read_time(prompt):
    while True:
        value = input(prompt).strip()

        try:
            parsed = datetime.strptime(value, "%H:%M")
            if parsed.strftime("%H:%M") == value:
                return parsed
        except ValueError:
            pass

        print("Enter a valid 24-hour time, e.g. 09:50.")


def enter_timetable():
    print("\n--- Enter / Update Timetable ---")

    reg_no = input("Enter your college Reg No.: ").strip()

    if not reg_no:
        print("Reg No. cannot be empty.")
        return

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT reg_no FROM Students WHERE reg_no = %s",
            (reg_no,)
        )

        if cursor.fetchone() is None:
            print("Student not found. Register first.")
            return

        cursor.execute(
            """
            SELECT timetable_id
            FROM Timetables
            WHERE reg_no = %s
            ORDER BY timetable_id DESC
            LIMIT 1
            """,
            (reg_no,)
        )

        result = cursor.fetchone()

        if result:
            timetable_id = result[0]
            cursor.execute(
                "DELETE FROM Classes WHERE timetable_id = %s",
                (timetable_id,)
            )
            cursor.execute(
                """
                UPDATE Timetables
                SET image_path = NULL, status = 'uploaded'
                WHERE timetable_id = %s
                """,
                (timetable_id,)
            )
        else:
            cursor.execute(
                """
                INSERT INTO Timetables (reg_no, image_path, status)
                VALUES (%s, NULL, 'uploaded')
                """,
                (reg_no,)
            )
            timetable_id = cursor.lastrowid

        for day_name, day_number in DAYS:
            print(f"\n--- {day_name} ---")

            if day_name == "Sunday":
                print("No classes on Sunday. Skipping.")
                continue

            lab_count = read_integer(
                f"How many labs on {day_name}? ",
                0,
                20
            )

            day_labs = []

            for lab_number in range(1, lab_count + 1):
                while True:
                    start = read_time(
                        f"Lab {lab_number} start time (HH:MM): "
                    )
                    end = start + timedelta(
                        minutes=LAB_DURATION_MINUTES
                    )

                    if end.date() != start.date():
                        print("Lab cannot extend past midnight.")
                        continue

                    overlaps = any(
                        start < existing_end and end > existing_start
                        for existing_start, existing_end in day_labs
                    )

                    if overlaps:
                        print("This lab overlaps another lab.")
                        continue

                    break

                day_labs.append((start, end))
                print(
                    f"Lab {lab_number}: "
                    f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"
                )

            day_labs.sort(key=lambda item: item[0])

            for lab_number, (start, end) in enumerate(day_labs, start=1):
                cursor.execute(
                    """
                    INSERT INTO Classes
                        (timetable_id, day_of_week,
                         start_time, end_time, subject)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        timetable_id,
                        day_number,
                        start.strftime("%H:%M:%S"),
                        end.strftime("%H:%M:%S"),
                        f"Lab {lab_number}"
                    )
                )

        conn.commit()
        print("\nTimetable saved successfully for", reg_no)

    except Exception as error:
        if conn:
            conn.rollback()
        print("Could not save timetable:", error)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    enter_timetable()
