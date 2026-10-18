
import hashlib
import secrets

from database import get_connection
from timetable import enter_timetable
from availability import check_student_availability
from tasks import manage_tasks


def hash_password(password):
    """Hash a password with a random salt."""
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000
    )
    return salt.hex() + "$" + password_hash.hex()


def register_student():
    print("\n--- Register Student ---")

    reg_no = input("College registration number: ").strip()
    name = input("Full name: ").strip()
    email = input("Email: ").strip()
    password = input("Create password: ")
    department = input("Department (optional): ").strip()
    semester_text = input("Semester (optional): ").strip()
    phone = input("Phone number (optional): ").strip()

    if not reg_no or not name or not email or not password:
        print("Reg No., name, email, and password are required.")
        return

    semester = None

    if semester_text:
        try:
            semester = int(semester_text)
            if semester <= 0:
                print("Semester must be positive.")
                return
        except ValueError:
            print("Semester must be a number.")
            return

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO Students
                (reg_no, name, email, password_hash,
                 department, semester, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reg_no,
                name,
                email,
                hash_password(password),
                department or None,
                semester,
                phone or None
            )
        )

        conn.commit()
        print("\nRegistration successful!")
        print("Reg No.:", reg_no)

    except Exception as error:
        if conn:
            conn.rollback()
        print("Registration failed:", error)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def main():
    while True:
        print("\n========== CAMPUSHELP ==========")
        print("1. Register Student")
        print("2. Enter / Update Timetable")
        print("3. Check Student Availability")
        print("4. Manage Tasks")
        print("5. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            register_student()

        elif choice == "2":
            enter_timetable()

        elif choice == "3":
            check_student_availability()

        elif choice == "4":
            manage_tasks()

        elif choice == "5":
            print("Thank you for using CampusHelp!")
            break

        else:
            print("Invalid choice. Choose 1–5.")


if __name__ == "__main__":
    main()
