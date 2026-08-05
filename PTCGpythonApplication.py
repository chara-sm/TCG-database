import sqlite3
our_db = "PTCGmanager.db"

#one time use, useless now
def create_tables():
    with open("PTCGmanagerTables.sql", "r") as file:
        sql_script = file.read()

    conn = sqlite3.connect(our_db)
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

def hash(text):
    hash_value = 5381 #seed

    for char in text:
        hash_value = ((hash_value << 5) + hash_value) + ord(char)

    return hash_value & 0xFFFFFFFF

def login(email, password):
    conn = sqlite3.connect(our_db)
    cursor = conn.cursor()

    query = "SELECT EXISTS (SELECT 1 FROM )"

def logout():
    pass

def main():
    pass

main()