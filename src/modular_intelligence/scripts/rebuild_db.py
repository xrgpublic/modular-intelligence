from modular_intelligence.database.config import Config
from modular_intelligence.database.init_db import init_database

def rebuild_database(dir_path=Config.DATABASE, schema_path=Config.SCHEMA_PATH):
    """ Deletes the database and reinitializes it """
    init_database(rebuild=True, dir_path=dir_path, schema_path=schema_path)


if __name__ == "__main__":
    rebuild_database()
