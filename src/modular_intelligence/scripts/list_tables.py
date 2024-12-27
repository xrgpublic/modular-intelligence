import sqlite3
from colorama import init, Fore, Style
from tabulate import tabulate
from modular_intelligence.database.config import Config
from modular_intelligence.database.init_db import init_database
import pprint
from tabulate import tabulate
import json

# Initialize colorama
init(autoreset=True)
init_database()

def print_database_output(data):
    # If data is a list of dictionaries
    if isinstance(data, list):
        print(pprint.pformat(data))  # Pretty print the list
    elif isinstance(data, dict):
        print(pprint.pformat(data))  # Pretty print the dictionary
    else:
        print("Data format not recognized.")

# If you have tabular data
def print_tabular_data(data):
    if isinstance(data, list) and all(isinstance(row, dict) for row in data):
        table = [list(row.values()) for row in data]
        print(tabulate(table, headers="keys"))  # Print as a table

# If you are dealing with JSON data
def print_json_data(data):
    print(json.dumps(data, indent=4))  # Pretty print JSON

def truncate_text(text, max_length=50):
    if text and len(text) > max_length:
        return text[:max_length] + "..."
    return text

def list_table_contents(table_name, cursor):
    print(f"\n{Fore.CYAN}=== Contents of {table_name} ==={Style.RESET_ALL}")
    try:
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get all rows
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if rows:
            # Truncate long text in the rows
            formatted_rows = []
            for row in rows:
                formatted_row = [truncate_text(str(cell)) if isinstance(cell, str) else cell for cell in row]
                formatted_rows.append(formatted_row)
            print(tabulate(formatted_rows, headers=columns, tablefmt="grid"))
        else:
            print(f"{Fore.YELLOW}No records found in this table.{Style.RESET_ALL}")
    except sqlite3.Error as e:
        print(f"{Fore.RED}Error accessing {table_name}: {e}{Style.RESET_ALL}")

def get_table_schema(table_name, cursor):
    print(f"\n{Fore.GREEN}=== Schema of {table_name} ==={Style.RESET_ALL}")
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        headers = ["CID", "Name", "Type", "NotNull", "DefaultValue", "PK"]
        print(tabulate(columns, headers=headers, tablefmt="grid"))
        
        # Show foreign keys if any
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = cursor.fetchall()
        if foreign_keys:
            print(f"\n{Fore.BLUE}Foreign Keys:{Style.RESET_ALL}")
            headers = ["ID", "Seq", "Table", "From", "To", "OnUpdate", "OnDelete", "Match"]
            print(tabulate(foreign_keys, headers=headers, tablefmt="grid"))
    except sqlite3.Error as e:
        print(f"{Fore.RED}Error getting schema for {table_name}: {e}{Style.RESET_ALL}")

def main():
    try:
        # Connect to the database
        conn = sqlite3.connect(Config.DATABASE)
        cursor = conn.cursor()
        
        # First show schemas
        print(f"\n{Fore.CYAN}=== Database Schema ==={Style.RESET_ALL}")
        for table in Config.TABLES:
            get_table_schema(table, cursor)
        
        # Then show contents
        print(f"\n{Fore.CYAN}=== Database Contents ==={Style.RESET_ALL}")
        for table in Config.TABLES:
            list_table_contents(table, cursor)
            
        
        
        # Close the database connection
    except sqlite3.Error as e:
        print(f"{Fore.RED}Database error: {e}{Style.RESET_ALL}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()
