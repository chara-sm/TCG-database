import sqlite3, hashlib, hmac, os, math
from tabulate import tabulate
from datetime import date

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

def secure_hash(text:str): # searched up how to make
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

def fetch_table_schema(table_name):
    schema_map = {}

    try:
        conn = sqlite3.connect(OUR_DB)
        cursor = conn.cursor()

        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        row_sql = cursor.fetchone()
        table_sql = row_sql[0].upper() if row_sql and row_sql[0] else ""
        has_autoincrement = "AUTOINCREMENT" in table_sql

        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()
        
        unique_columns = set()
        for idx in indexes:
            # idx[2] is the unique flag
            if idx[2] == 1:
                idx_name = idx[1]
                cursor.execute(f"PRAGMA index_info({idx_name})")
                for col_row in cursor.fetchall():
                    # col_row[2] contains the column name
                    unique_columns.add(col_row[2])

        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()

        for col_id, name, col_type, notnull, dflt_value, pk in rows:
            col_type = col_type.upper()
            is_unique = 1 if name in unique_columns or pk == 1 else 0
            is_autoincrement = 1 if pk == 1 and has_autoincrement else 0

            if "INT" in col_type:
                schema_map[name] = int, notnull, pk, is_unique, is_autoincrement, dflt_value
            elif "REAL" in col_type:
                schema_map[name] = float, notnull, pk, is_unique, is_autoincrement, dflt_value
            else:
                schema_map[name] = str, notnull, pk, is_unique, is_autoincrement, dflt_value
    except sqlite3.Error as e:
        print("Error fetching table schema:", e)
    except Exception as e:
        print("Error fetching table schema:", e)
    finally:
        cursor.close()
        conn.close()

    return schema_map

def data_dict_clean(data_dict, rules):
    clean_data_dict = {}

    for field, value in data_dict.items():
        datatype = rules[field][0]

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

def add_record(table_name, data_dict=None, is_user=False):
    if table_name in ['Log', 'Staff'] and is_user:
        print("Cannot add staff/log records as a user!")
        return False

    if data_dict is None:
        data_dict = {}

    success = False

    try:
        conn = sqlite3.connect(OUR_DB)
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys = ON")

        rules = fetch_table_schema(table_name)

        if is_user:
            terminal_output = f"Creating {table_name}:"

            for col, (datatype, notnull, pk, is_unique, is_autoincrement, dflt_value) in rules.items():
                has_dflt = dflt_value is not None
                is_required = (notnull or pk) and not has_dflt
                required_text = " [REQUIRED]" if is_required else ""

                dflt_value = date.today().isoformat() if dflt_value == "CURRENT_DATE" else dflt_value
                dflt_text = f" [DEFAULTS TO: '{dflt_value}']" if has_dflt else ""
                unique_text = f" [UNIQUE]" if is_unique else ""

                prompt = f"{col} [{datatype.__name__.upper()}]{required_text}{unique_text}{dflt_text}: "

                if is_autoincrement:
                    next_id_query = f"SELECT seq + 1 FROM sqlite_sequence WHERE name = ?"
                    cursor.execute(next_id_query, (table_name,))
                    next_id = cursor.fetchone()[0]

                    terminal_output += f"\n{prompt}{next_id}"
                    continue

                while True:
                    clear_terminal()
                    print(terminal_output)

                    field_value = input(prompt).strip()

                    if field_value == "":
                        if is_required:
                            print(f"[{col}] is required!")
                            input("> Press enter to continue ")
                            continue
                        else:
                            terminal_output += f"\n{prompt}{dflt_value}"
                            break

                    if field_value.upper() == "NULL":
                        if notnull or pk:
                            print(f"[{col}] is required!")
                            input("> Press enter to continue ")
                            continue
                        field_value = None

                    if field_value is not None:
                        if "password" in col.lower():
                            field_value = str(secure_hash(field_value))
                        else:
                            try:
                                field_value = datatype(field_value)
                            except ValueError as e:
                                print(f"Wrong datatype! Expected: {datatype.__name__.upper()}")
                                input("> Press enter to continue ")
                                continue

                    if is_unique and field_value is not None:
                        exists_query = f'SELECT EXISTS (SELECT 1 FROM "{table_name}" WHERE {col} = ?)'
                        cursor.execute(exists_query, (field_value,))
                        exists = bool(cursor.fetchone()[0])

                        if exists:
                            print(f"'{col} = {field_value}' already exists in {table_name}!")
                            print("Please enter another value.")
                            input("> Press enter to continue ")
                            continue

                    data_dict[col] = field_value

                    value_text = "NULL" if field_value is None else field_value
                    terminal_output += f"\n{prompt}{value_text}"
                    break

        clean_data_dict = data_dict_clean(data_dict, rules)
        insert_fields = ", ".join(clean_data_dict)

        values = tuple(clean_data_dict.values())
        values_placeholder = ", ".join(
            ["?"] * len(values) 
        )

        query = f'INSERT INTO "{table_name}" ({insert_fields}) VALUES ({values_placeholder})'
        cursor.execute(query, values)
        conn.commit()
        success = True
    except sqlite3.Error as e:
        print("Error adding record (SQL):", e)
    except Exception as e:
        print("Error adding record:", e)
    finally:
        cursor.close()
        conn.close()

    return success

def edit_record(table_name, conditions_dict, data_dict=None, is_user=False):
    if table_name in ['Log', 'Staff'] and is_user:
        print("Cannot edit staff/log records as a user!")
        return False

    if data_dict is None:
        data_dict = {}

    success = False

    try:
        conn = sqlite3.connect(OUR_DB)
        cursor = conn.cursor()

        where_values = tuple(conditions_dict.values())
        where_clause = " WHERE " + " AND ".join(
            f"{field} = ?" for field in conditions_dict.keys()
        )

        rules = fetch_table_schema(table_name)

        if is_user:
            terminal_output = "Editing [" + " = ".join(
                f"{field} = {value}" for field, value in conditions_dict.items()
            ) + "]"
            
            for col, (datatype, notnull, pk, is_unique, is_autoincrement, dflt_value) in rules.items():
                current_value_query = f"SELECT {col} FROM {table_name}{where_clause}"
                cursor.execute(current_value_query, where_values)
                current_value = cursor.fetchone()[0]

                current_value_text = f" [CURRENT: {current_value}]"
                unique_text = f" [UNIQUE]" if is_unique else ""
                prompt = f"{col} [{datatype.__name__.upper()}]{current_value_text}{unique_text}: "

                if is_autoincrement:
                    terminal_output += f"\n{prompt}{current_value}"
                    continue

                while True:
                    clear_terminal()
                    print(terminal_output)

                    field_value = input(prompt).strip()

                    if field_value == "":
                        terminal_output += f"\n{prompt}{current_value}"
                        break

                    if field_value.upper() == "NULL":
                        if notnull or pk:
                            print(f"[{col}] is required!")
                            input("> Press enter to continue ")
                            continue
                        field_value = None

                    if field_value is not None:
                        if "password" in col.lower():
                            field_value = str(secure_hash(field_value))
                        else:
                            try:
                                field_value = datatype(field_value)
                            except ValueError as e:
                                print(f"Wrong datatype! Expected: {datatype.__name__.upper()}")
                                input("> Press enter to continue ")
                                continue

                    if is_unique and field_value is not None:
                        exists_query = f'SELECT EXISTS (SELECT 1 FROM "{table_name}" WHERE {col} = ?)'
                        cursor.execute(exists_query, (field_value,))
                        exists = bool(cursor.fetchone()[0])

                        if exists:
                            print(f"'{col} = {field_value}' already exists in {table_name}!")
                            print("Please enter another value.")
                            input("> Press enter to continue ")
                            continue

                    data_dict[col] = field_value

                    value_text = "NULL" if field_value is None else field_value
                    terminal_output += f"\n{prompt}{value_text}"
                    break

        clean_data_dict = data_dict_clean(data_dict, rules)

        if not clean_data_dict:
            print("No changes were entered.")
            return False

        set_values = tuple(clean_data_dict.values())
        set_placeholder = ", ".join(
            f"{field} = ?" for field in clean_data_dict.keys()
        )

        values = set_values + where_values

        query = f"UPDATE {table_name} SET {set_placeholder}{where_clause}"
        cursor.execute(query, values)
        conn.commit()
        success = True
    except sqlite3.Error as e:
        print("Error editing data (SQL):", e)
    except Exception as e:
        print("Error editing data:", e)
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

        prompt = f"Are you sure you want to delete {num_of_rows_to_del} records from {table_name}? [Y/N]\n> "
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
        col_names = list(fetch_table_schema(table_name).keys())
    else:
        print("Error in displaying records: No column names or table name was given!")
        return success

    try:
        table = tabulate(records, headers=col_names, tablefmt="fancy_grid", maxcolwidths=20)
        print(table)
        success = True
    except Exception as e:
        print("Error in displaying records", e)

    return success

def search_and_display_records(table_name, conditions_dict={}, limit=10, fields_required=None, is_user=False):
    try:
        page = 1
        max_page = math.ceil(count_rows(table_name=table_name, conditions_dict=conditions_dict)/limit)
        ans = ""

        while True:
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
                case _ if "back" in ans:
                    return
                case _:
                    print("Not a valid option/page!")
                    input("> Press enter to continue ")
    except Exception as e:
        print("Error in displaying tables in page view:", e)

def build_conditions_dict(table_name):
    rules = fetch_table_schema(table_name)
    conditions_dict = {}

    terminal_output = "Conditions:"

    try:
        for col, (datatype, notnull, pk, is_unique, is_autoincrement, dflt_value) in rules.items():
            prompt = f"{col} [{datatype.__name__.upper()}]: "

            while True:
                clear_terminal()
                print(terminal_output)

                field_value = input(prompt).strip()

                if field_value == "":
                    terminal_output += f"\n{prompt}"
                    break

                if field_value.upper() == "NULL":
                    if notnull or pk:
                        print(f"[{col}] is required!")
                        input("> Press enter to continue ")
                        continue
                    field_value = None

                if field_value is not None:
                    if "password" in col.lower():
                        field_value = str(secure_hash(field_value))
                    else:
                        try:
                            field_value = datatype(field_value)
                        except ValueError as e:
                            print(f"Wrong datatype! Expected: {datatype.__name__.upper()}")
                            input("> Press enter to continue ")
                            continue

                conditions_dict[col] = field_value

                value_text = "NULL" if field_value is None else field_value
                terminal_output += f"\n{prompt}{value_text}"
                break
    except Exception as e:
        print(f"Error building conditions dictionary:", e)

    return conditions_dict

def manage_players():
    # inner functions
    def view_all_players():
        search_and_display_records("Player", is_user=True)

    def register_player():
        success = add_record("Player", is_user=True)
        if success:
            print("Successfully registered player!")
            input("> Press enter to continue ")
        else:
            print("Error registering player.")
            input("> Press enter to continue ")

    def edit_player():
        while True:
            clear_terminal()
            
            try:
                print("Enter [back] to return.")
                user_ans = input("Enter PlayerID to edit: ").strip().lower()

                if "back" in user_ans:
                    return
                else:
                    if user_ans == "":
                        condition_dict = {}
                    else:
                        condition_dict = {"PlayerID": int(user_ans)}
                    success = edit_record("Player", conditions_dict=condition_dict, is_user=True)

                    if success:
                        print(f"\nSuccessfully edited player ({user_ans})")
                    else:
                        print(f"\nFailed to edit player ({user_ans})")

                    input("> Press enter to continue ")
                    return
                    
            except ValueError as e:
                print("PlayerID must be an integer:", e)
                input("> Press enter to continue ")

    def delete_player():
        while True:
            clear_terminal()
            
            try:
                print("Enter [back] to return.")
                user_ans = input("Enter PlayerID to delete: ").strip().lower()

                if "back" in user_ans:
                    return
                else:
                    if user_ans == "":
                        condition_dict = {}
                    else:
                        condition_dict = {"PlayerID": int(user_ans)}
                    success = delete_record("Player", conditions_dict=condition_dict, is_user=True)

                    if success:
                        print(f"\nSuccessfully deleted player ({user_ans})")
                    else:
                        print(f"\nFailed to delete player ({user_ans})")

                    input("> Press enter to continue ")
                    return
                    
            except ValueError as e:
                print("PlayerID must be an integer:", e)
                input("> Press enter to continue ")

    def search_for_players():
        conditions_dict = build_conditions_dict("Player")
        search_and_display_records("Player", conditions_dict=conditions_dict, is_user=True)

    ans = ""

    while True:
        clear_terminal()

        print("Manager Players")
        print(SEPARATOR)
        print("""0. Go back
1. View all players
2. Register a new player
3. Edit an existing player's data
4. Delete an existing player
5. Search for player(s)""")
        print(SEPARATOR)

        try:
            ans = int(input("> "))

            match ans:
                case 0:
                    return
                case 1:
                    view_all_players()
                case 2:
                    register_player()
                case 3:
                    edit_player()
                case 4:
                    delete_player()
                case 5:
                    search_for_players()
                case _:
                    print("Not a valid option!")
                    input("> Press enter to continue ")
        except ValueError as e:
            print("Please input an integer.")
            input("> Press enter to continue ")

def manage_cards():
    # inner functions
    def view_all_cards():
        search_and_display_records("Card", is_user=True)

    def add_new_card():
        success = add_record("Card", is_user=True)
        if success:
            print("Successfully adding card!")
            input("> Press enter to continue ")
        else:
            print("Error adding card.")
            input("> Press enter to continue ")

    def edit_card():
        while True:
            clear_terminal()
            
            try:
                print("Enter [back] to return.")
                user_ans = input("Enter CardID to edit: ").strip().lower()

                if "back" in user_ans:
                    return
                else:
                    if user_ans == "":
                        condition_dict = {}
                    else:
                        condition_dict = {"CardID": int(user_ans)}
                    success = edit_record("Card", conditions_dict=condition_dict, is_user=True)

                    if success:
                        print(f"\nSuccessfully edited card ({user_ans})")
                    else:
                        print(f"\nFailed to edit card ({user_ans})")

                    input("> Press enter to continue ")
                    return
                    
            except ValueError as e:
                print("CardID must be an integer:", e)
                input("> Press enter to continue ")

    def delete_card():
        while True:
            clear_terminal()
            
            try:
                print("Enter [back] to return.")
                user_ans = input("Enter CardID to delete: ").strip().lower()

                if "back" in user_ans:
                    return
                else:
                    if user_ans == "":
                        condition_dict = {}
                    else:
                        condition_dict = {"CardID": int(user_ans)}
                    success = delete_record("Card", conditions_dict=condition_dict, is_user=True)

                    if success:
                        print(f"\nSuccessfully deleted card ({user_ans})")
                    else:
                        print(f"\nFailed to delete card ({user_ans})")

                    input("> Press enter to continue ")
                    return
                    
            except ValueError as e:
                print("PlayerID must be an integer:", e)
                input("> Press enter to continue ")

    def search_for_cards():
        conditions_dict = build_conditions_dict("Card")
        search_and_display_records("Card", conditions_dict=conditions_dict, is_user=True)
        
    ans = ""

    while True:
        clear_terminal()

        print("Manage Cards")
        print(SEPARATOR)
        print("""0. Go back
1. View all cards
2. Add a new card
3. Edit an existing card
4. Delete an existing card
5. Search for card(s)""")
        print(SEPARATOR)

        try:
            ans = int(input("> "))

            match ans:
                case 0:
                    return
                case 1:
                    view_all_cards()
                case 2:
                    add_new_card()
                case 3:
                    edit_card()
                case 4:
                    delete_card()
                case 5:
                    search_for_cards()
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
            case 2:
                manage_cards()
            case 7:
                search_and_display_records("Log")
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
            current_user_passwordhash = str(secure_hash(current_user_passwordhash.strip()))

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