import sqlite3

def create_tables():
    with open("PTCGmanagerTables.sql", "r") as file:
        sql_script = file.read()

    conn = sqlite3.connect("PTCGmanager.db")
    cursor = conn.cursor()

    try:
        cursor.executescript(sql_script)
        conn.commit()
        print("Tables created successfully")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

create_tables()