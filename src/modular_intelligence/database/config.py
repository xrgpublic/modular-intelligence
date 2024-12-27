import os
from pathlib import Path

class Config:
    APP_NAME = "modular_intelligence"
    DATABASE = Path.home() / f".{APP_NAME}" / f"{APP_NAME}.db"
    DEBUG = True
    PORT = 5000
    ENABLE_FOREIGN_KEYS = True
    SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')
    TABLES = {
    'BOTS': 'Bots',
    'CHECKPOINTS': 'Checkpoints',
    'STACKS': 'Stacks',
    'STACKSLOTS': 'StackSlots'
    }
    QDRANT_COLLECTION_NAME = "assistant_memory"
    VECTOR_SIZE = 768

    # Add any additional configuration settings here
    SQLITE_URI = f'sqlite:///{DATABASE}'
