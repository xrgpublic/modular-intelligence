-- Drop existing tables if they exist
DROP TABLE IF EXISTS StackSlots;
DROP TABLE IF EXISTS Stacks;
DROP TABLE IF EXISTS Checkpoints;
DROP TABLE IF EXISTS Bots;
DROP TABLE IF EXISTS Sessions;

-- Enable foreign key constraint support
PRAGMA foreign_keys = ON;

-- Create Bots table with orchestrator_bot flag
CREATE TABLE IF NOT EXISTS Bots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    default_system_prompt TEXT,
    system_prompt TEXT,
    model TEXT,
    orchestrator_bot INTEGER NOT NULL DEFAULT 0 CHECK (orchestrator_bot IN (0, 1))
);

-- Create Checkpoints table
CREATE TABLE IF NOT EXISTS Checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id INTEGER NOT NULL,
    checkpoint_number INTEGER NOT NULL,
    version TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    system_prompt TEXT,
    datasets JSON,
    memories JSON,
    session_history JSON,
    model TEXT,
    name TEXT,
    description TEXT,
    FOREIGN KEY (bot_id) REFERENCES Bots(id) ON DELETE CASCADE
    
);

-- Create Sessions table
CREATE TABLE IF NOT EXISTS Sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id INTEGER NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    messages TEXT NOT NULL,
    FOREIGN KEY (bot_id) REFERENCES Bots (id)
);

-- Create Stacks table
CREATE TABLE IF NOT EXISTS Stacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    orchestrator_bot_id INTEGER,
    FOREIGN KEY (orchestrator_bot_id) REFERENCES Bots(id) ON DELETE SET NULL
);

-- Create StackSlots table
CREATE TABLE IF NOT EXISTS StackSlots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stack_id INTEGER NOT NULL,
    slot_number INTEGER NOT NULL CHECK(slot_number BETWEEN 1 AND 5),
    bot_id INTEGER,
    bot_checkpoint_id INTEGER,
    FOREIGN KEY (stack_id) REFERENCES Stacks(id) ON DELETE CASCADE,
    FOREIGN KEY (bot_id) REFERENCES Bots(id) ON DELETE CASCADE,
    FOREIGN KEY (bot_checkpoint_id) REFERENCES Checkpoints(id) ON DELETE CASCADE
);
