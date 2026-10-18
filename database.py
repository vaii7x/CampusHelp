
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="3133",
        database="campushelp"
    )

if __name__ == "__main__":
    try:
        conn = get_connection()
        print("CampusHelp database connected successfully!")
        conn.close()
    except mysql.connector.Error as err:
        print("Connection failed:", err)
