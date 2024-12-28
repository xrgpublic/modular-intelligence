from modular_intelligence.agents import BaseAgent
from modular_intelligence.scripts.list_tables import list_tables

def init_bots():
    """" Create a basic bot """

    # Create a new bot instance
    bot = BaseAgent(name="AssistantBot", description="A friendly assistant.", prompt="You are a helpful assistant.")

    # Optionally, add datasets and memories
    # bot.add_dataset([...])
    # bot.add_memory([...])
    # More information on datasets and memories can be found in the documentation [ https://github.com/xrgpu/modular-intelligence/wiki/Creating-Bots ]

    # Start a session ( This will create a new save for your bot. This will also load any datasets and memories into the bot's context window )
    bot.start_session()

    # Save the bot to the database and creates a checkpoint of the current state. ( Use 'status' to change the name of the checkpoint's save )
    bot.save_to_db(status="Custom Checkpoint Name")

    # Lets simmulate a conversation
    # generate_response can do a lot. Please view the documentation [ https://github.com/xrgpu/modular-intelligence/wiki/Generating-Responses ]
    bot.generate_response("Hello, how are you?")

    #You can disable API calls by setting test_mode to True
    bot.test_mode = True
    bot.generate_response("What is the capital of France?")

    # End the session ( This will create a new save for your bot )
    bot.end_session()

    # Prints tables.  You can find the tables in 'database\nuts.db' . You will need a sqlite viewer to view it. This is the vscode extension I use: Name: [SQLite Viewer](https://open-vsx.org/vscode/item?itemName=qwtel.sqlite-viewer)
    # Alternatively you can use the companian app for modular intelligence: [AI Observability](https://github.com/xrgpu/modular-intelligence-ai-observability)
    list_tables()

if __name__ == "__main__":
    init_bots() # Runs the script