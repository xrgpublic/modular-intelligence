"""
Dynamic Stack Implementation

This module provides the AgentStack class for managing agent hierarchies with database integration
and replication capabilities.
"""

import sqlite3
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager
from modular_intelligence.agents.base import BaseAgent

@dataclass
class StackSlot:
    id: Optional[int]
    stack_id: int
    slot_number: int
    bot_id: Optional[int]

class AgentStack:
    def __init__(self, db_path: str, name: str = "", description: str = ""):
        """Initialize a new stack instance.
        
        Args:
            db_path: Path to the SQLite database
            name: Name of the stack
            description: Description of the stack
        """
        self.db_path = db_path
        self.name = name
        self.description = description
        self.id: Optional[int] = None
        
    @contextmanager
    def _get_db(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def create(self, orchestrator_bot_id: Optional[int] = None) -> bool:
        """Create a new stack in the database.
        
        Args:
            orchestrator_bot_id: Optional ID of the orchestrator bot
            
        Returns:
            bool: True if creation was successful
        """
        if not orchestrator_bot_id:
            orchestrator_bot = self.create_orchestrator()
            orchestrator_bot_id = orchestrator_bot.id
            print(f"Orchestrator bot created with ID: {orchestrator_bot_id}")
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO Stacks (name, description, orchestrator_bot_id)
                VALUES (?, ?, ?)
                """,
                (self.name, self.description, orchestrator_bot_id)
            )
            self.id = cursor.lastrowid
            conn.commit()
            return True
            
    def add_slot(self, bot: BaseAgent, bot_checkpoint: Optional[int] = None, slot_number: Optional[int] = None) -> Optional[StackSlot]:
        """Add a new slot to the stack.
        
        Args:
            bot: Bot object to assign to this slot
            bot_checkpoint: Optional ID of the bot checkpoint to assign to this slot
            slot_number: Optional number of the slot (1-5). If not provided, next available slot will be used
            
        Returns:
            StackSlot: Created slot object if successful, None otherwise
            
        Raises:
            ValueError: If stack is not created, or if specified slot number is invalid
        """
        if not self.id:
            raise ValueError("Stack must be created first")
        
        with self._get_db() as conn:
            cursor = conn.cursor()
            if bot_checkpoint is None:
                # Find most recent checkpoint for bot
                cursor.execute('SELECT id FROM Checkpoints WHERE bot_id = ? ORDER BY checkpoint_number DESC LIMIT 1', (bot.id,))
                bot.checkpoint_id = cursor.fetchone()[0]
            else:
                bot.checkpoint_id = bot_checkpoint
            if slot_number is None:
                # Find next available slot
                cursor.execute('SELECT slot_number FROM StackSlots WHERE stack_id = ?', (self.id,))
                used_slots = [row[0] for row in cursor.fetchall()]
                for num in range(1, 6):
                    if num not in used_slots:
                        slot_number = num
                        break
                if slot_number is None:
                    raise ValueError("No available slots in stack")
            elif not 1 <= slot_number <= 5:
                raise ValueError("Slot number must be between 1 and 5")
            
            cursor.execute(
                """
                INSERT INTO StackSlots (stack_id, slot_number, bot_id, bot_checkpoint_id)
                VALUES (?, ?, ?, ?)
                """,
                (self.id, slot_number, bot.id, bot.checkpoint_id)
            )
            conn.commit()
            return StackSlot(
                id=cursor.lastrowid,
                stack_id=self.id,
                slot_number=slot_number,
                bot_id=bot.id
            )
            
    def replicate(self, new_name: Optional[str] = None) -> 'AgentStack':
        """Create a copy of this stack with all its slots.
        
        Args:
            new_name: Optional new name for the replicated stack
            
        Returns:
            AgentStack: New stack instance
        """
        if not self.id:
            raise ValueError("Cannot replicate an uncreated stack")
            
        new_stack = AgentStack(
            self.db_path,
            name=new_name or f"{self.name}_copy",
            description=f"Replica of {self.name}"
        )
        
        with self._get_db() as conn:
            # Create new stack
            new_stack.create()
            
            # Copy all slots
            cursor = conn.cursor()
            slots = cursor.execute(
                "SELECT * FROM StackSlots WHERE stack_id = ?",
                (self.id,)
            ).fetchall()
            
            for slot in slots:
                new_stack.add_slot(slot['bot_id'], slot['slot_number'])
                
        return new_stack
    
    def get_slots(self) -> List[StackSlot]:
        """Get all slots in this stack.
        
        Returns:
            List[StackSlot]: List of slot objects
        """
        if not self.id:
            return []
            
        with self._get_db() as conn:
            cursor = conn.cursor()
            slots = cursor.execute(
                "SELECT * FROM StackSlots WHERE stack_id = ? ORDER BY slot_number",
                (self.id,)
            ).fetchall()
            
            return [
                StackSlot(
                    id=slot['id'],
                    stack_id=slot['stack_id'],
                    slot_number=slot['slot_number'],
                    bot_id=slot['bot_id']
                )
                for slot in slots
            ]
            
    def get_slot(self, slot_number: int) -> Optional[StackSlot]:
        """Get a specific slot in this stack.
        
        Args:
            slot_number: Number of the slot to retrieve (1-5)
            
        Returns:
            StackSlot: Slot object if found, None otherwise
        """
        if not self.id:
            return None
            
        with self._get_db() as conn:
            cursor = conn.cursor()
            slot = cursor.execute(
                "SELECT * FROM StackSlots WHERE stack_id = ? AND slot_number = ?",
                (self.id, slot_number)
            ).fetchone()
            
            if not slot:
                return None
                
            return StackSlot(
                id=slot['id'],
                stack_id=slot['stack_id'],
                slot_number=slot['slot_number'],
                bot_id=slot['bot_id']
            )

    def load(self, db_path: str, stack_id: int) -> 'AgentStack':
        """Load an existing stack from the database.
        
        Args:
            db_path: Path to the SQLite database
            stack_id: ID of the stack to load
            
        Returns:
            AgentStack: Loaded stack instance
        """
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            stack_data = cursor.execute(
                "SELECT * FROM Stacks WHERE id = ?",
                (stack_id,)
            ).fetchone()
            
            if not stack_data:
                raise ValueError(f"No stack found with ID {stack_id}")
                
            self.id = stack_id
            self.name = stack_data['name']
            self.description = stack_data['description']
            return stack_data
    
    def create_orchestrator(self):
        """Create the orchestrator bot for this stack."""
        orchestrator = BaseAgent(
            name="Orchestrator",
            description="Orchestrator bot for this stack",
            system_prompt="You are an orchestrator bot for a stack of AI agents. You coordinate the interactions between the agents in the stack.",
            orchestrator_bot=True,
            stack_id=self.id
        )
        orchestrator.save_to_db()
        print(f"Orchestrator bot created with ID: {orchestrator.id}")
        return orchestrator

    def train_orchestrator(self):
        """Train the orchestrator bot for this stack."""
        pass

    def update(self, new_name: Optional[str] = None, new_description: Optional[str] = None):
        """Update the stack's name and description."""
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Stacks SET name = ?, description = ? WHERE id = ?",
                (new_name or self.name, new_description or self.description, self.id)
            )
            conn.commit()

        
