import sqlite3, hashlib, hmac, os

# # # Constants
OUR_DB = "PTCGmanager.db"
HASH_SECRET_KEY = "612ftr8#%71nvvmr1BH@51i_rq2vh0H!VNIinIUH671!*(Paf]awdn"
SEPARATOR = "---------------------------------"

# # # Global variables
logged_in = False
current_user_email = ""
current_user_passwordhash = ""

# # # Functions
def clear_terminal(): # searched up
    # Use 'cls' for Windows (nt) and 'clear' for Mac and Linux
    os.system('cls' if os.name == 'nt' else 'clear')

def hash(text:str): # searched up how to make
    key_bytes = HASH_SECRET_KEY.encode('utf-8')
    text_bytes = text.encode('utf-8')

    hashed_obj = hmac.new(
        key_bytes,
        text_bytes,
        hashlib.sha256
    )

    return hashed_obj.hexdigest()

def login(email:str, passwordhash:str):
    conn = sqlite3.connect(OUR_DB)
    cursor = conn.cursor()
    
    query = "SELECT EXISTS (SELECT 1 FROM Staff WHERE Email = ? AND PasswordHash = ?)"
    cursor.execute(query, (email, passwordhash))
    exists = bool(cursor.fetchone()[0]) # will be true if fetchone tuple is not empty

    cursor.close()  
    conn.close()

    return exists

def logout():
    pass

def add_record(table_name, data_dict):
    if table_name == "Log": return False

    values = ", ".join(
        
    )

def search_table(table_name, conditions_dict, fields_required=None):

    conn = sqlite3.connect(OUR_DB)
    cursor = conn.cursor()

    if fields_required:
        if type(fields_required) is str:
            select_condition = fields_required
        else:
            select_condition = ", ".join(
                field for field in fields_required
            )
    else:
        select_condition = "*"

    results = None

    try:
        if conditions_dict:
            where_condition = " AND ".join(
                f"{field} = ?" for field in conditions_dict
            )

            values = tuple(conditions_dict.values())
            query = f"SELECT {select_condition} FROM {table_name} WHERE {where_condition}"

            cursor.execute(query, values)
            results = cursor.fetchall()
        else:
            query = f"SELECT {select_condition} FROM {table_name}"
            cursor.execute(query)
            results = cursor.fetchall()
    except sqlite3.Error as e:
        print("Search table failed:", e)

    cursor.close()
    conn.close()

    return results

def home_page():
    clear_terminal()
    print(SEPARATOR)
    result = search_table("Staff", {"Email": current_user_email, "PasswordHash": current_user_passwordhash}, ["FirstName", "LastName"])
    FirstName, LastName = result[0][0], result[0][1]
    
    print(f"Hello there, {FirstName} {LastName}.")
    print(SEPARATOR)
    print("What would you like to do?")

    print("""
1. View tables
2. Search tables
3. Add records
4. Edit records
5. Delete records
          """)

    input()

def main():
    global logged_in, current_user_email, current_user_passwordhash

    # Handle log in
    while not logged_in:
        clear_terminal()

        print(SEPARATOR)
        print("Welcome to the Pokemon TCG manager!")
        print(SEPARATOR)
        print("Login Page")

        # Fetch user details
        current_user_email = input("Email:")
        current_user_passwordhash = input("Password:")

        # Sanitise input
        current_user_email = current_user_email.strip().lower()
        current_user_passwordhash = str(hash(current_user_passwordhash.strip()))

        # Attempt login
        logged_in = login(current_user_email, current_user_passwordhash)

        clear_terminal()

        # Print message accordingly
        print("Sucessful login!" if logged_in else "Your details do not match anything in our system.")
        input("> Press enter to continue ")

    # Handle main manager
    while logged_in:
        home_page()

main()