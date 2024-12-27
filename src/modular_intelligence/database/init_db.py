import sqlite3
from modular_intelligence.database.config import Config
import os

def init_database(rebuild=False, dir_path=Config.DATABASE, schema_path=Config.SCHEMA_PATH):
            
    # Delete database if it exists and rebuild is requested
    if rebuild:
        if os.path.exists(dir_path):
            os.remove(dir_path)
    
    # return if database already exists
    if os.path.isfile(dir_path):
        print("Database already exists!")
        return

    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(dir_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Connect to database
    db_connection = sqlite3.connect(dir_path)
    cursor = db_connection.cursor()
    
    # Enable foreign keys
    if Config.ENABLE_FOREIGN_KEYS:
        cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Read and execute schema
    print("Initializing database...",schema_path)
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    
    # Commit changes and close connection
    db_connection.commit()
    db_connection.close()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
