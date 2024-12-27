"""
Base Agent Module

This module contains the BaseAgent class which provides core functionality
for all agent types in the Dynamic Swarm system.
"""

import sqlite3
from datetime import datetime
from ollama import generate, chat
from colorama import init, Fore, Style
import json
from modular_intelligence.database.config import Config

class BaseAgent:
    def __init__(self, db_path=Config.DATABASE, name="default name", description="default description", 
                 default_system_prompt="You are a helpful AI Assistant.", orchestrator_bot=False,
                 system_prompt=None, datasets=None, memories=None, session_history=None,
                 stack_id=None, test_mode=False, model="llama3.2", **kwargs):
        if not name or not isinstance(name, str):
            raise ValueError("The 'name' must be a non-empty string.")
        if not description or not isinstance(description, str):
            raise ValueError("The 'description' must be a non-empty string.")
        if not default_system_prompt or not isinstance(default_system_prompt, str):
            raise ValueError("The 'default_system_prompt' must be a non-empty string.")
        
        # Bot properties
        self.id = None  # Will be set when saving to DB
        self.name = name
        self.description = description
        self.default_system_prompt = default_system_prompt
        self.orchestrator_bot = orchestrator_bot
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        
        # Checkpoint properties
        self.system_prompt = system_prompt or default_system_prompt
        self.datasets = datasets if datasets else []
        self.memories = memories if memories else []
        self.session_history = session_history if session_history else []
        self.session_messages = [{"role": "system", "content": self.system_prompt}]
        
        # Other properties
        self.rank = None  # For stack-specific ranking
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.datetime = datetime
        self.generate = generate
        self.chat = chat
        self.color = Fore.GREEN # Will be color that is printed to Terminal
        self.stack_id = stack_id
        self.test_mode = test_mode
        self.checkpoint_id = kwargs.get("checkpoint_id", None)

        # Autonomoy Flags
        self.dynamic_memory = False
        
    def reset_session(self):
        """
        Resets the session by clearing all session messages.
        """
        self.end_session(status="reset_session ( ended session )")
        self.session_messages = [{"role": "system", "content": self.system_prompt}]
        self.session_history = [{"role": "system", "content": self.system_prompt}]
        self.start_session(status="reset_session ( started session )")
        print("Session has been reset.")

    def clear_session_messages(self, role=None):
        """
        Clears session messages for a specific role (user or assistant) or all if role is not specified.

        Parameters:
        role (str, optional): The role whose messages should be cleared. Options are 'user' or 'assistant'.
        """
        if role:
            self.session_messages = [msg for msg in self.session_messages if msg["role"] != role]
            print(f"Session messages for role '{role}' have been cleared.")
        else:
            self.session_messages = [{"role": "system", "content": self.system_prompt}]
            print("Session messages have been cleared.")
        self.session_history = self.session_messages

    def _add_to_list(self, target_list, content, type_name=None):
        """
        Adds content to the target list after performing type checking.

        Parameters:
        target_list (list): The list where the content should be added.
        content (list or dict): A list of dictionaries or a single dictionary.
        type_name (str, optional): The name of the target list (e.g. 'dataset' or 'memory'). Defaults to None.

        Raises:
        ValueError: If the content is not a list or if the content is a list but it is empty.
        ValueError: If the content is a list but the first item is not a dictionary.
        ValueError: If the content is a dictionary but it does not contain 'title', 'description', and 'messages' keys.
        """
        if isinstance(content, list) and len(content) > 1 and isinstance(content[0], dict):
            title = content[0].get("title")
            description = content[0].get("description")
            content_messages = content[1:]
        if all(isinstance(item, dict) for item in content_messages):
            target_list.append({"title": title, "description": description, "messages": content_messages})
        else:
            raise ValueError(f"{type_name} content must be a list of dictionaries after the title and description.")
        
    def add_dataset(self, dataset):
        """
        Adds a dataset to the bot's datasets.

        Parameters:
        dataset (list of dict): Dataset in list of dictionaries format to be added to the bot's knowledge. The dataset should include a title and description, which are not added to the AI's context window.
        
        Example:
        dataset = [
            {"title": "dataset title", "description": "Dataset description"},
            {"role": "user", "content": "Sample user response"},
            {"role": "assistant", "content": "Sample assistant response"},
            {"role": "user", "content": "Sample user response"}
        ]
        """
        self._add_to_list(self.datasets, dataset, "Dataset")

    def add_memory(self, memory):
        """
        Adds a memory to the bot's memories.

        Parameters:
        memory (list of dict): Memory in list of dictionaries format to be added to the bot's knowledge. The memory should include an optional title and description, which are not added to the AI's context window.
        
        Example:
        memory = [
            {"title": "memory title", "description": "Memory description"},
            {"role": "user", "content": "User greeted the assistant"},
            {"role": "assistant", "content": "Assistant greeted back"}
        ]
        """
        self._add_to_list(self.memories, memory, "Memory")

    def start_session(self, memories_first=False, status="start_session"):
        """
        Starts a new session by initializing the session messages with the system prompt,
        and appending messages from datasets and memories based on the specified order.

        This method prepares the [session_messages] list, which includes the system prompt,
        followed by either dataset messages or memory messages, depending on the value of
        the `memories_first` flag.

        Parameters:
            memories_first (bool): A flag that determines the order of message addition.
                If True, memory messages are added before dataset messages. If False,
                dataset messages are added first.

        The method will:
        - Initialize the [session_messages] with the system prompt.
        - Collect messages from the datasets and memories.
        - Append the collected messages to [session_messages]in the specified order.
        - Save the current session state to the database after the session is started.
        """

        # Gets the current system prompt
        self.session_messages = [{"role": "system", "content": self.system_prompt}]

        # Prepare the message lists
        dataset_messages = []
        memory_messages = []

        # Populate dataset messages
        if self.datasets:
            for dataset in self.datasets:
                dataset_messages.extend(dataset["messages"])

        # Populate memory messages
        if self.memories:
            for memory in self.memories:
                # We'll just collect them in order and decide how to prepend/append later
                memory_messages.extend(memory["messages"])

        # Decide the order based on the `memories_first` flag
        if memories_first:
            self.session_messages = memory_messages + self.session_messages + dataset_messages
            return
        self.session_messages = self.session_messages + dataset_messages + memory_messages
    
        self.session_history = self.session_messages
        # Save the current session state
        self.save_to_db(status=status)

    def end_session(self, status="end_session"):
        """
        Ends the session and saves the bot's current state to the database.
        """
        print(f"Session has been ended for {self.name}.")
        self.save_to_db(status=status)

    def save_to_db(self, status="update", create_checkpoint=True):
        """
        Saves the bot's current state to the database and optionally creates a checkpoint.
        """
        if self.id is None:
            # First check if a bot with this name already exists
            self.cursor.execute("""
                SELECT id FROM Bots WHERE name = ?
            """, (self.name,))
            existing_bot = self.cursor.fetchone()
            
            if existing_bot:
                self.id = existing_bot[0]
            else:
                # If no existing bot found, create a new one
                self.cursor.execute("""
                    INSERT INTO Bots (name, description, default_system_prompt, system_prompt, model, orchestrator_bot)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.name,
                    self.description,
                    self.default_system_prompt,
                    self.system_prompt,
                    self.model,
                    1 if self.orchestrator_bot else 0
                ))
                self.conn.commit()
                self.id = self.cursor.lastrowid
        else:
            # Update the bot's information
            self.cursor.execute("""
                UPDATE Bots
                SET name = ?, description = ?, default_system_prompt = ?, system_prompt = ?, model = ?, orchestrator_bot = ?
                WHERE id = ?
            """, (
                self.name,
                self.description,
                self.default_system_prompt,
                self.system_prompt,
                self.model,
                1 if self.orchestrator_bot else 0,
                self.id
            ))
            self.conn.commit()
        
        # Create a checkpoint if requested
        if create_checkpoint:
            self.create_checkpoint(f"{status} checkpoint for {self.name}")
            
    def create_checkpoint(self, version):
        """
        Creates a new checkpoint with the current state.
        """
        if not self.id:
            raise ValueError("Bot must be saved to database before creating checkpoint")

        next_checkpoint = self.cursor.execute(
                'SELECT COALESCE(MAX(checkpoint_number), 0) + 1 FROM Checkpoints WHERE bot_id = ?',
                (self.id,)
            ).fetchone()[0]
            
        self.cursor.execute("""
            INSERT INTO Checkpoints (bot_id, checkpoint_number, version, system_prompt, datasets, memories, session_history, model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.id,
            next_checkpoint,
            version,
            self.system_prompt,
            json.dumps(self.datasets),
            json.dumps(self.memories),
            json.dumps(self.session_history),
            self.model
        ))
        self.conn.commit()
            
    def load_from_db(self, name=None, bot_id=None, checkpoint_id=None):
        """
        Loads the bot's data from the database using either bot_id or name.
        Optionally loads a specific checkpoint's data.

        Parameters:
        name (str, optional): Name of the bot to load
        bot_id (int, optional): ID of the bot to load
        checkpoint_id (int, optional): ID of the checkpoint to load
        """
        if not name and not bot_id:
            raise ValueError("Either name or bot_id must be provided")

        # First load bot data
        if bot_id:
            self.cursor.execute('SELECT * FROM Bots WHERE id = ?', (bot_id,))
        else:
            self.cursor.execute('SELECT * FROM Bots WHERE name = ?', (name,))
        
        bot = self.cursor.fetchone()
        if not bot:
            raise ValueError(f"Bot not found: {'id=' + str(bot_id) if bot_id else 'name=' + name}")

        # Update bot properties
        self.id = bot[0]
        self.name = bot[1]
        self.description = bot[2]
        self.default_system_prompt = bot[3]
        self.orchestrator_bot = bot[4] == 1

        # Load checkpoint data
        if checkpoint_id:
            self.cursor.execute('SELECT * FROM Checkpoints WHERE id = ? AND bot_id = ?', (checkpoint_id, self.id))
        else:
            # Load most recent checkpoint
            self.cursor.execute('''
                SELECT * FROM Checkpoints 
                WHERE bot_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (self.id,))
        
        checkpoint = self.cursor.fetchone()
        if checkpoint:
            self.system_prompt = checkpoint[5] or self.default_system_prompt
            self.datasets = json.loads(checkpoint[6]) if checkpoint[6] else []
            self.memories = json.loads(checkpoint[7]) if checkpoint[7] else []
            self.session_history = json.loads(checkpoint[8]) if checkpoint[8] else []
            self.session_messages = json.loads(checkpoint[8]) if checkpoint[8] else []
            self.model = checkpoint[9]
        else:
            # No checkpoint found, use default values
            self.system_prompt = self.default_system_prompt
            self.datasets = []
            self.memories = []
            self.session_history = []
            self.session_messages = [{"role": "system", "content": self.system_prompt}]

        return self.id

    def load_from_dict(self, bot_dict):
        """
        Loads bot attributes from a dictionary representation.

        Parameters:
        bot_dict (dict): Dictionary with bot details.
        """
        self.name = bot_dict.get("name", self.name)
        self.description = bot_dict.get("description", self.description)
        self.default_system_prompt = bot_dict.get("default_system_prompt", self.default_system_prompt)
        self.orchestrator_bot = bot_dict.get("orchestrator_bot", self.orchestrator_bot)

    def to_dict(self):
        """
        Converts the bot's attributes into a dictionary representation.

        Returns:
        dict: Dictionary with bot details.
        """
        return {
            "name": self.name,
            "description": self.description,
            "default_system_prompt": self.default_system_prompt,
            "orchestrator_bot": self.orchestrator_bot,
        }

    def save_bot(self, filepath):
        """
        Saves the bot's details to a file in JSON format.

        Parameters:
        filepath (str): File path where the bot details will be saved.
        """
        with open(filepath, 'w') as file:
            json.dump(self.to_dict(), file)

    def load_bot(self, filepath):
        """
        Loads the bot's details from a JSON file.

        Parameters:
        filepath (str): File path from which the bot details will be loaded.
        """
        with open(filepath, 'r') as file:
            bot_dict = json.load(file)
            self.load_from_dict(bot_dict)
            
    def dict_to_json(self, dictionary, output_file=None):
        """
        Converts a dictionary to JSON format.

        Parameters:
            dictionary (dict): The dictionary to convert.
            output_file (str, optional): File path to save the JSON. Defaults to None.

        Returns:
            str: The JSON string if no output file is specified.
        """
        try:
            # Convert dictionary to JSON string
            json_data = json.dumps(dictionary, indent=4)
        
            if output_file:
                # Save JSON to a file if an output file is specified
                with open(output_file, 'w') as file:
                    file.write(json_data)
                print(f"JSON saved to {output_file}")
            else:
                # Return the JSON string if no file is specified
                return json_data
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def print_all(self, debug_mode=False):
        """
        Prints all messages in the session, including AI responses and user inputs.

        Parameters:
        debug_mode (bool): If True, prints the full bot state as JSON. Defaults to False.
        """
        for msg in self.session_messages:
            name_suffix = f": ({self.name})" if msg['role'] == 'assistant' else ""
            print(f"\n[{msg['role'].upper()}]{name_suffix}")
            print(msg['content'])
            print("-" * 50) 
            
        # Only show the full JSON if needed for debugging
        if debug_mode:
            print("\n=== AI Context Window ===")
            print(f"\n{self.name} Memory:")
            print(f"\n=== Full {self.name} Bot State (JSON) ===")
            # Format session messages with consistent key order
            # formatted_state = self.to_dict()
            # formatted_state['session_messages'] = [
            #     {'role': msg['role'], 'content': msg['content']} 
            #     for msg in formatted_state['session_messages']
            # ]
            # print(f"{self}:\n{self.dict_to_json(formatted_state)}\n")

    def prompt_adjuster(self):
        """
        Generates a refined and optimized system prompt for another AI agent
        based on the user's input, the specific task requested, and the existing
        AI agent's prompt.

        Returns:
        str: The refined system prompt.
        """
        if self.test_mode:
            return
        response = chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': f'''
### **System Prompt**

#### **Role**:
You are an AI agent specialized in enhancing, modifying, or completely re-creating prompts for other AI agents. Your purpose is to analyze the user's input, the specific task requested, and the existing AI agent's prompt to generate a refined and optimized system prompt.

#### **Objectives**:
1. **Analyze**: Break down the user's input and task requirements to identify key goals, constraints, and nuances.
2. **Evaluate**: Assess the current AI agent’s prompt for clarity, relevance, structure, and alignment with the task.
3. **Enhance**: Modify the prompt to address any deficiencies, ensuring it is perfectly tailored for the intended purpose.
4. **Iterate**: Use feedback or insights to make incremental improvements until the system prompt achieves perfection.

#### **Process**:
1. Receive:
   - The **user's input** (describing the task or problem).
   - The **task details** (specific requirements and goals).
   - The **current AI's prompt** (as it stands before modification).
2. Extract:
   - Core objectives of the task.
   - Weaknesses or areas of improvement in the current prompt.
   - Opportunities for enhancement or complete re-creation.
3. Generate:
   - A refined or new system prompt that achieves 100% alignment with the task requirements.
4. Verify:
   - Ensure the final system prompt is clear, concise, and structured to optimize the AI agent's performance.

#### **Guidelines**:
- **Language**: Use precise, unambiguous language with no room for misinterpretation.
- **Structure**: Organize the prompt into clear sections for roles, objectives, processes, and context.
- **Relevance**: Ensure every element of the prompt directly contributes to fulfilling the user’s request.
- **Iteration Limit**: Continue improving the prompt for up to 100 iterations or until the user confirms satisfaction.

#### **Output Format**:
Return the refined prompt in the following format:
```
### System Prompt: Iteration [X]
[Content of the enhanced or re-created prompt]
```
'''},
{'role': 'user', 'content': f'''
### User Input:
{self.default_system_prompt}'''}]
        )
        self.default_system_prompt = response['message']['content']
        # Update the system prompt in session_messages
        self.session_messages[0]['content'] = self.default_system_prompt

    @classmethod
    def create_from_bot(cls, source_bot_name, new_bot_name, new_description, db_path, checkpoint_number=None, checkpoint_name=None):
        """
        Creates a new bot instance from a specified checkpoint of an existing bot.
        The checkpoint can be specified either by number or by name.
        If neither is specified, uses the most recent checkpoint.
        Checkpoint numbers start from 0, with 0 being the oldest checkpoint.

        Parameters:
        source_bot_name (str): Name of the source bot to create from
        new_bot_name (str): Name for the new bot
        new_description (str): Description for the new bot
        db_path (str): Path to the database
        checkpoint_number (int, optional): Number of the checkpoint to use (0 is oldest). If None, uses most recent.
        checkpoint_name (str, optional): Name of the checkpoint to use. Takes precedence over checkpoint_number if both are provided.

        Returns:
        BaseAgent: A new bot instance with the state from the specified checkpoint
        """
        # Create database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get the source bot's ID
        cursor.execute("SELECT id FROM Bots WHERE name = ?", (source_bot_name,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Source bot '{source_bot_name}' not found")
        source_bot_id = result[0]

        # Get total number of checkpoints
        cursor.execute("""
            SELECT COUNT(*) FROM Checkpoints WHERE bot_id = ?
        """, (source_bot_id,))
        total_checkpoints = cursor.fetchone()[0]

        if total_checkpoints == 0:
            raise ValueError(f"No checkpoints found for bot '{source_bot_name}'")

        # If checkpoint_name is provided, use it
        if checkpoint_name is not None:
            cursor.execute("""
                SELECT default_system_prompt, orchestrator_bot
                FROM Checkpoints 
                WHERE bot_id = ? AND name = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (source_bot_id, checkpoint_name))
            checkpoint = cursor.fetchone()
            if not checkpoint:
                raise ValueError(f"No checkpoint found with name '{checkpoint_name}'")
        else:
            # If checkpoint_number is specified, validate it
            if checkpoint_number is not None:
                if not isinstance(checkpoint_number, int):
                    raise ValueError("checkpoint_number must be an integer")
                if checkpoint_number < 0 or checkpoint_number >= total_checkpoints:
                    raise ValueError(f"Invalid checkpoint_number. Must be between 0 and {total_checkpoints - 1}")

                cursor.execute("""
                    SELECT default_system_prompt, orchestrator_bot
                    FROM Checkpoints 
                    WHERE bot_id = ?
                    ORDER BY timestamp ASC
                    LIMIT 1 OFFSET ?
                """, (source_bot_id, checkpoint_number))
            else:
                # Get most recent checkpoint
                cursor.execute("""
                    SELECT default_system_prompt, orchestrator_bot
                    FROM Checkpoints 
                    WHERE bot_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (source_bot_id,))

            checkpoint = cursor.fetchone()

        if not checkpoint:
            print(f"DEBUG - Total checkpoints: {total_checkpoints}, Checkpoint number: {checkpoint_number}")
            raise ValueError(f"Failed to retrieve checkpoint for bot '{source_bot_name}'")

        # Create new bot with checkpoint data
        new_bot = cls(
            db_path=db_path,
            name=new_bot_name,
            description=new_description,
            default_system_prompt=checkpoint[0],
            orchestrator_bot=checkpoint[1] == 1
        )

        # Save the new bot to database
        new_bot.save_to_db(status="start_session")

        return new_bot

# --------------- USER COMMANDS ---------------
    def generate_response(self, user_input, max_length=2000, throttle_delay=0, model=None, print_user=True, save_response=True, create_checkpoint=False):
        """
        Processes user input and generates a response from the assistant model.

        This method adds the user's input to the session messages and history, 
        throttles the response generation based on the specified delay, and 
        retrieves a response from the assistant model. The response can be 
        optionally saved to the session messages and history.

        Parameters:
        - user_input (str): The input message from the user.
        - max_length (int): The maximum length of the generated response. Default is 2000.
        - throttle_delay (int): The delay in seconds before generating a response. Default is 0.
        - model (str): The model to use for generating the response. Default is "llama3.2".
        - print_user (bool): Whether to print the user's input to the console. Default is True.
        - save_response (bool): Whether to save the assistant's response to the session. Default is True.

        Returns:
        - str: The generated response from the assistant, or an error message if the response generation fails.
        """
        # Add user input to both session messages and history
        user_message = {'role': 'user', 'content': user_input}
        session_hist = self.session_history
        self.session_history = session_hist#syncing the session history with 
        self.session_messages.append(user_message)

        import time
        time.sleep(throttle_delay)  # Throttle response
        
        if print_user:
            print(f"{Fore.WHITE}USER:\n{user_input}")
            
        try:
            if self.test_mode:
                content = "This is a test mode response. Ollama is disabled."
                print(f"\n{self.color}ASSISTANT({self.name}):\n{content}\n{Fore.RESET}")
                assistant_message = {'role': 'assistant', 'content': content}
            else:
                response = chat(
                    model=model or self.model,
                    messages=self.session_messages
                )
                if response and 'message' in response and 'content' in response['message']:
                    content = response['message']['content']
                    print(f"\n{self.color}ASSISTANT({self.name}):\n{content}\n{Fore.RESET}")
                    assistant_message = {'role': 'assistant', 'content': content}
                else:
                    raise ValueError("Invalid response format")
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            content = 'Error processing response'
            assistant_message = {'role': 'assistant', 'content': content}
        
        # Add assistant response to both session messages and history
        if not save_response:
            self.session_messages.pop()
            return content
        else:
            self.session_messages.append(assistant_message)
        
        # Save the updated state to the database
        self.save_to_db(status="chat", create_checkpoint=create_checkpoint)
        
        return content
    
    # Wrapper.  Just loads the first checkpoint
    def reset(self):
        self.load_from_db(bot_id=self.id, checkpoint_id=0)

    # Can forget any number of messages, if all is true, forgets everything
    def forget(self, messages_to_forget=2, all=False, save_system_prompt=False, save_datasets=False, save_memories=False, save_session_history=False):
        """
        Forgets a specified number of messages from the session or all messages based on the parameters.

        This method allows the agent to forget either a specific number of messages from the session 
        messages or all messages, along with options to retain the system prompt, datasets, memories, 
        and session history. The state is saved to the database after the operation.

        Parameters:
        - messages_to_forget (int): The number of messages to forget from the session. Default is 2.
        - all (bool): If True, forgets all messages instead of a specified number. Default is False.
        - save_system_prompt (bool): If True, retains the current system prompt when forgetting all messages. Default is False.
        - save_datasets (bool): If True, retains the datasets when forgetting all messages. Default is False.
        - save_memories (bool): If True, retains the memories when forgetting all messages. Default is False.
        - save_session_history (bool): If True, retains the session history when forgetting all messages. Default is False.

        Returns:
        - str: A message indicating the result of the operation when forgetting all messages.
        - list: A list of forgotten messages when forgetting a specified number of messages.
        """
        if all:
            self.system_prompt, new_prompt = self.system_prompt if save_system_prompt else self.default_system_prompt
            self.session_messages = [{"role": "system", "content": new_prompt}]
            self.datasets = self.datasets if save_datasets else []
            self.memories = self.memories if save_memories else []
            self.session_history = self.session_history if save_session_history else []
            self.save_to_db(status="Forgot all")
            return "All messages have been forgotten."
        
        else:
            forgotten_messages = []
            for _ in range(messages_to_forget):
                if self.session_messages:
                    forgotten_messages.append(self.session_messages.pop())
            self.save_to_db(status=f"Forgot {messages_to_forget} messages.", create_checkpoint=False)
            return forgotten_messages
        