import sqlite3, hashlib, hmac, os, math
from tabulate import tabulate

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
    exists = False

    try:
        conn = sqlite3.connect(OUR_DB)
        cursor = conn.cursor()

        query = "SELECT EXISTS (SELECT 1 FROM Staff WHERE Email = ? AND PasswordHash = ?)"
        cursor.execute(query, (email, passwordhash))
        exists = bool(cursor.fetchone()[0]) # will be true if fetchone tuple is not empty
    except sqlite3.Error as e:
        print(f"Error in logging in:", e)
    finally:
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

    try:
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
    except sqlite3.Error as e:
        print("Error fetching columns:", e)
    except Exception as e:
        print("Error cleaning data:", e)
    finally:
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

def count_rows(table_name, conditions_dict={}):
    num_of_rows = None

    try:
        conn = sqlite3.connect(OUR_DB)
        cursor = conn.cursor()

        if conditions_dict:
            where_clause = " WHERE " + " AND ".join(
                f"{field} = ?" for field in conditions_dict
            )
            values = tuple(conditions_dict.values())
        else:
            where_clause = ""
            values = ()

        select_query = f"SELECT COUNT(*) FROM {table_name}{where_clause}"
        cursor.execute(select_query, values)
        num_of_rows = cursor.fetchone()[0]
    except sqlite3.Error as e:
        print("Error deleting data:", e)
    except Exception as e:
        print("Error cleaning data:", e)
    finally:
        cursor.close()
        conn.close()

    return num_of_rows

def add_record(table_name, data_dict, is_user=False):
    if table_name in ['Log', 'Staff'] and is_user:
        print("Cannot add staff/log records as a user!")
        return False

    success = False

    try:
        conn = sqlite3.connect(OUR_DB)
        cursor = conn.cursor()

        rules = get_column_types(table_name)

        clean_data_dict = data_dict_clean(data_dict, rules)

        insert_fields = ", ".join(clean_data_dict)

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
        print("Error cleaning data:", e)
    finally:
        cursor.close()
        conn.close()

    return success

def edit_record(table_name, conditions_dict, is_user=False):
    if table_name in ['Log', 'Staff'] and is_user:
        print("Cannot edit staff/log records as a user!")
        return False

    success = False
    data_dict = {}

    try:
        conn = sqlite3.connect(OUR_DB)
        cursor = conn.cursor()

        rules = get_column_types(table_name)

        for col in rules.keys():
            field_value = input(f"{col}: ").strip()

            if field_value:
                if field_value.upper() == "NULL":
                    data_dict[col] = None
                else:
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
        print("Error cleaning data:", e)
    finally:
        cursor.close()
        conn.close()

    return success

def delete_record(table_name, conditions_dict, is_user=False):
    if table_name in ['Log', 'Staff'] and is_user:
        print("Cannot delete staff/log records as a user!")
        return False
    
    success = False

    try:
        conn = sqlite3.connect(OUR_DB)
        cursor = conn.cursor()

        if conditions_dict:
            where_clause = " WHERE " + " AND ".join(
                f"{field} = ?" for field in conditions_dict
            )
            values = tuple(conditions_dict.values())
        else:
            where_clause = ""
            values = ()

        num_of_rows_to_del = count_rows(table_name=table_name, conditions_dict=conditions_dict)

        prompt = f"Are you sure you want to delete {num_of_rows_to_del} records from {table_name}?"
        confirmation = input(prompt).strip().lower()
        while confirmation not in ['y','n']:
            print("Please enter [Y/N].")
            confirmation = input(prompt).strip().lower()

        if confirmation == "y":
            delete_query = f"DELETE FROM {table_name}{where_clause}"
            cursor.execute(delete_query, values)
            conn.commit()
            success = True
    except sqlite3.Error as e:
        print("Error deleting data:", e)
    except Exception as e:
        print("Error cleaning data:", e)
    finally:
        cursor.close()
        conn.close()

    return success

def search_table(table_name, conditions_dict={}, limit=10, offset=0, fields_required=[], is_user=False):
    if table_name == 'Staff' and is_user:
        print("Cannot search staff records as a user!")
        return False

    results = []

    try:
        conn = sqlite3.connect(OUR_DB)
        cursor = conn.cursor()

        if fields_required:
            if isinstance(fields_required, str):
                select_condition = fields_required
            else:
                select_condition = ", ".join(fields_required)
        else:
            select_condition = "*"

        if conditions_dict:
            where_clause = " WHERE " + " AND ".join(
                f"{field} = ?" for field in conditions_dict
            )
            values = tuple(conditions_dict.values())
        else:
            where_clause = ""
            values = ()

        if limit:
            limit_clause = f" LIMIT {limit}"
        else:
            limit_clause = ""

        if offset:
            offset_clause = f" OFFSET {offset}"
        else:
            offset_clause = ""

        query = f"SELECT {select_condition} FROM {table_name}{where_clause}{limit_clause}{offset_clause}"
        cursor.execute(query, values)
        results = cursor.fetchall()
    except sqlite3.Error as e:
        print("Search table failed:", e)
    finally:
        cursor.close()
        conn.close()

    return results

def display_records(records, col_names=None, table_name=None):
    success = False

    if col_names:
        col_names = [col_names] if isinstance(col_names, str) else col_names
    elif table_name:
        col_names = list(get_column_types(table_name).keys())
    else:
        print("Error in displaying records: No column names or table name was given!")
        return success

    try:
        table = tabulate(records, headers=col_names, tablefmt="fancy_grid")
        print(table)
        success = True
    except Exception as e:
        print("Error in displaying records", e)

    return success

def search_and_display_records(table_name, conditions_dict={}, limit=10, fields_required=[], is_user=False):
    try:
        page = 1
        max_page = math.ceil(count_rows(table_name=table_name, conditions_dict=conditions_dict)/limit)
        ans = None

        while ans != "back":
            clear_terminal()
            current_offset = limit * (page-1)

            records = search_table(table_name, conditions_dict=conditions_dict, limit=limit, offset=current_offset, fields_required=fields_required, is_user=is_user)
            display_records(records, fields_required, table_name)

            print(f"""Press enter to continue to the next page,
Or enter a page number,
Or enter [back] to return.
Page: ({page}/{max_page})
""")
            ans = input("> ").strip().lower()

            match ans:
                case "" if page < max_page:
                    page += 1
                case _ if ans.isdigit() and 0 < int(ans) <= max_page:
                    page = int(ans)
                case "back":
                    return
                case _:
                    print("Not a valid option/page!")
                    input("> Press enter to continue ")
    except Exception as e:
        print("Error in displaying tables in page view:", e)

def manage_players():
    # inner functions
    def view_all_players():
        search_and_display_records("Player", is_user=True)

    ans = None

    while True:
        clear_terminal()

        print("Manager Players")
        print(SEPARATOR)
        print("""0. Go back
1. View all players
2. Register a new player
3. Edit an existing player's data
4. Delete an existing player""")
        print(SEPARATOR)

        try:
            ans = int(input("> "))

            match ans:
                case 0:
                    return
                case 1:
                    view_all_players()
                case _:
                    print("Not a valid option!")
                    input("> Press enter to continue ")
        except ValueError as e:
            print("Please input an integer.")
            input("> Press enter to continue ")

def home_page():
    clear_terminal()
    result = search_table("Staff", {"Email": current_user_email, "PasswordHash": current_user_passwordhash}, fields_required=["FirstName", "LastName"])

    if result:
        FirstName, LastName = result[0][0], result[0][1]
    else:
        FirstName, LastName = "Staff", "Member"
    
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

    try:
        ans = int(input("> "))

        match ans:
            case 1:
                manage_players()
            case 8:
                logout()
            case _:
                print("Not a valid option!")
                input("> Press enter to continue ")
    except ValueError as e:
        print("Please input an integer.")
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