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
    global logged_in, current_user_email, current_user_passwordhash

    logged_in = False
    current_user_email = ""
    current_user_passwordhash = ""

    clear_terminal()
    print("Successfully logged out!")
    input("> Press enter to continue ")

    return True

def get_column_types(table_name):
    schema_map = {}

    conn = sqlite3.connect(OUR_DB)
    cursor = conn.cursor()

    query = f"SELECT name, type FROM PRAGMA_TABLE_INFO('{table_name}')"
    cursor.execute(query)
    rows = cursor.fetchall()

    for name, col_type in rows:
        col_type = col_type.upper()
        if "INT" in col_type:
            schema_map[name] = int
        elif "REAL" in col_type:
            schema_map[name] = float
        else:
            schema_map[name] = str

    cursor.close()
    conn.close()

    return schema_map

def data_dict_clean(data_dict, rules):
    clean_data_dict = {}

    for field, value in data_dict.items():
        datatype = rules[field]

        if value is None:
            clean_data_dict[field] = None
        else:
            value = str(value).strip()
            clean_data_dict[field] = datatype(value)

    return clean_data_dict

def add_record(table_name, data_dict, is_user=False):
    if table_name == "Log" and is_user:
        print("Cannot add records into logs as a user!")
        return False

    conn = sqlite3.connect(OUR_DB)
    cursor = conn.cursor()
    success = False

    try:
        rules = get_column_types(table_name)

        clean_data_dict = data_dict_clean(data_dict, rules)

        insert_fields = ", ".join(
            field for field in clean_data_dict
        )

        values = tuple(clean_data_dict.values())
        values_placeholder = ", ".join(
            ["?"] * len(values) 
        )

        query = f"INSERT INTO {table_name} ({insert_fields}) VALUES ({values_placeholder})"
        cursor.execute(query, values)
        conn.commit()
        success = True
    except sqlite3.Error as e:
        print("Error inserting data:", e)
    except Exception as e:
        print("Error in cleaning data:", e)
    finally:
        cursor.close()
        conn.close()

    return success

def edit_record(table_name, conditions_dict, is_user=False):
    if (table_name == "Log" or table_name == "Staff") and is_user:
        print("Cannot edit staff/log records as a user!")
        return False

    conn = sqlite3.connect(OUR_DB)
    cursor = conn.cursor()
    success = False
    
    data_dict = {}

    try:
        rules = get_column_types(table_name)

        for col in rules.keys():
            field_value = input(f"{col}: ").strip()

            if field_value:
                data_dict[col] = field_value

        clean_data_dict = data_dict_clean(data_dict, rules)

        if not clean_data_dict:
            print("No changes were entered.")
            return False

        set_values = tuple(clean_data_dict.values())
        set_placeholder = ", ".join(
            f"{field} = ?" for field in clean_data_dict.keys()
        )

        where_values = tuple(conditions_dict.values())
        where_condition = " AND ".join(
            f"{field} = ?" for field in conditions_dict.keys()
        )

        values = set_values + where_values

        query = f"UPDATE {table_name} SET {set_placeholder} WHERE {where_condition}"
        cursor.execute(query, values)
        conn.commit()
        success = True
    except sqlite3.Error as e:
        print("Error editing data:", e)
    except Exception as e:
        print("Error in cleaning data:", e)
    finally:
        cursor.close()
        conn.close()

    return success

def search_table(table_name, conditions_dict, fields_required=None):
    conn = sqlite3.connect(OUR_DB)
    cursor = conn.cursor()

    results = None

    try:
        if fields_required:
            if type(fields_required) is str:
                select_condition = fields_required
            else:
                select_condition = ", ".join(
                    field for field in fields_required
                )
        else:
            select_condition = "*"

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
    finally:
        cursor.close()
        conn.close()

    return results

def manage_players():
    ans = None

    while ans not in (1,2,3,4):
        clear_terminal()
        print("Manage Players")
        print(SEPARATOR)
        print("""1. View all players
2. Register a new player
3. Edit an existing player's data
4. Delete an existing player""")
        print(SEPARATOR)
        ans = input("> ")

        try:
            ans = int(ans)
        except ValueError as e:
            print("Please input a number.")
            input("> Press enter to continue ")

def home_page():
    clear_terminal()
    result = search_table("Staff", {"Email": current_user_email, "PasswordHash": current_user_passwordhash}, ["FirstName", "LastName"])
    FirstName, LastName = result[0][0], result[0][1]
    
    print(f"Hello there, {FirstName} {LastName}.")
    print(SEPARATOR)
    print("What would you like to do?")

    print("""
1. Manage Players
2. Manage Cards
3. Manage Card Sets
4. Manage Decks
5. Manage Tournaments
6. Manage Your Account
7. View Logs
8. Logout""")
    
    print(SEPARATOR)
    ans = input("> ")

    try:
        ans = int(ans)

        match ans:
            case 1:
                manage_players()
            case 8:
                logout()
            case _:
                print("Not a valid option!")
                input("> Press enter to continue ")
    except ValueError as e:
        print("Please input a number.")
        input("> Press enter to continue ")

def main():
    global logged_in, current_user_email, current_user_passwordhash

    while True:
    # Handle log in
        if not logged_in:
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

            # Print message accordingly
            print(SEPARATOR)
            print("Sucessful login!" if logged_in else "Your details do not match anything in our system.")
            input("> Press enter to continue ")

        # Handle main manager
        else:
            home_page()

main()