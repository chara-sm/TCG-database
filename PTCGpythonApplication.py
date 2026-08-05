import sqlite3, hashlib, hmac, secrets

# # # Constants
OUR_DB = "PTCGmanager.db"
HASH_SECRET_KEY = "612ftr8#%71nvvmr1BH@51i_rq2vh0H!VNIinIUH671!*(Paf]awdn"
SEPARATOR = "---------------------------------"

# # # Global variables
logged_in = False

# # # Functions
#one time use, useless now
def create_tables():
    with open("PTCGmanagerTables.sql", "r") as file:
        sql_script = file.read()

    conn = sqlite3.connect(OUR_DB)
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

def hash(text:str):
    key_bytes = HASH_SECRET_KEY.encode('utf-8')
    text_bytes = text.encode('utf-8')

    hashed_obj = hmac.new(
        key_bytes,
        text_bytes,
        hashlib.sha256
    )

    return hashed_obj.hexdigest()

def login(email:str, password:str):
    global logged_in

    conn = sqlite3.connect(OUR_DB)
    cursor = conn.cursor()

    hashed_password = str(hash(password))
    
    query = "SELECT EXISTS (SELECT 1 FROM Staff WHERE Email = ? AND PasswordHash = ?)"
    cursor.execute(query, (email, hashed_password))
    exists = bool(cursor.fetchone()[0])

    cursor.close()  
    conn.close()

    if exists:
        logged_in = True

    return exists

def logout():
    pass

def main():
    global logged_in

    print(SEPARATOR)
    print("Weolcome to the Pokemon TCG manager!")

    while True:
        print(SEPARATOR)
        print("Login Page")
        user_email = input("Email:")
        user_password = input("Password:")

        login(user_email, user_password)

        print(SEPARATOR)
        if logged_in:
            print("Successful login")
        else:
            print("Your details do not match anything in our system.")
        input("> Press enter to continue ")
        

main()