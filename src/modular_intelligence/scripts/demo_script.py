import sqlite3
import pandas as pd
from modular_intelligence.agents.base import BaseAgent
from modular_intelligence.database.config import Config
from modular_intelligence.database.init_db import init_database
from modular_intelligence.stack.stack import AgentStack
from modular_intelligence.scripts.conversations.convos_for_demo_script import get_conversations







# ==========================================================================================
# ------------------------------------- AGENT CREATION -------------------------------------
# ==========================================================================================

# Step 2: Create Agents
# Agent 1: MathTutor
def create_agents():
    agent1 = BaseAgent(
        name="MathTutor",
        description="An AI that helps with math problems.",
        default_system_prompt="You are a math tutor helping students understand mathematical concepts.",
        orchestrator_bot=False,
        test_mode=True
    )
    agent1.add_dataset([
        {"title": "Algebra Basics", "description": "Dataset for algebra problems"},
        {"role": "user", "content": "Solve for x: 2x + 3 = 7"},
        {"role": "assistant", "content": "Subtract 3: 2x = 4; Divide by 2: x = 2"}
    ])
    agent1.add_memory([
        {"title": "Session 1", "description": "Discussed quadratic equations"},
        {"role": "user", "content": "How to solve x^2 - 5x + 6 = 0?"},
        {"role": "assistant", "content": "Factor to (x-2)(x-3)=0; So x=2 or x=3"}
    ])

    # Repeat similar steps for agents 2 to 5 (omitted for brevity)
    # Agent 2: English Tutor
    agent2 = BaseAgent(
        name="EnglishTutor",
        description="An AI that helps with English grammar and writing.",
        default_system_prompt="You are an English tutor assisting students with grammar and composition.",
        orchestrator_bot=False,
        test_mode=True
    )

    agent2.add_dataset([
        {"title": "Grammar Rules", "description": "Dataset for English grammar"},
        {"role": "user", "content": "What is a noun?"},
        {"role": "assistant", "content": "A noun is a person, place, thing, or idea."}
    ])

    agent2.add_memory([
        {"title": "Session 1", "description": "Explained verb tenses"},
        {"role": "user", "content": "Explain past perfect tense."},
        {"role": "assistant", "content": "Past perfect is used for actions completed before another past action."}
    ])

    # Agent 3: Science Explainer
    agent3 = BaseAgent(
        name="ScienceExplainer",
        description="An AI that explains scientific concepts.",
        default_system_prompt="You are a science explainer making complex concepts easy to understand.",
        orchestrator_bot=False,
        test_mode=True
    )

    agent3.add_dataset([
        {"title": "Chemistry Basics", "description": "Dataset for basic chemistry"},
        {"role": "user", "content": "What is an atom?"},
        {"role": "assistant", "content": "An atom is the smallest unit of matter that retains the properties of an element."}
    ])

    agent3.add_memory([
        {"title": "Session 1", "description": "Discussed chemical bonds"},
        {"role": "user", "content": "Explain ionic bonds."},
        {"role": "assistant", "content": "Ionic bonds form when electrons are transferred from one atom to another."}
    ])

    # Agent 4: History Buff
    agent4 = BaseAgent(
        name="HistoryBuff",
        description="An AI that provides historical information.",
        default_system_prompt="You are a historian sharing knowledge about world history.",
        orchestrator_bot=False,
        test_mode=True
    )

    agent4.add_dataset([
        {"title": "Ancient Civilizations", "description": "Dataset on ancient history"},
        {"role": "user", "content": "Tell me about the Egyptian pyramids."},
        {"role": "assistant", "content": "The pyramids were monumental tombs built for pharaohs in ancient Egypt."}
    ])

    agent4.add_memory([
        {"title": "Session 1", "description": "Discussed World War I"},
        {"role": "user", "content": "What caused World War I?"},
        {"role": "assistant", "content": "It was triggered by the assassination of Archduke Franz Ferdinand."}
    ])

    # Agent 5: Code Helper
    agent5 = BaseAgent(
        name="CodeHelper",
        description="An AI that assists with programming questions.",
        default_system_prompt="You are a coding assistant helping users with programming challenges.",
        orchestrator_bot=False,
        test_mode=True
    )

    agent5.add_dataset([
        {"title": "Programming Basics", "description": "Dataset on programming fundamentals"},
        {"role": "user", "content": "What is a variable in programming?"},
        {"role": "assistant", "content": "A variable stores data values that can change during program execution."}
    ])

    agent5.add_memory([
        {"title": "Session 1", "description": "Explored loops in Python"},
        {"role": "user", "content": "How does a 'while' loop work?"},
        {"role": "assistant", "content": "It repeatedly executes code as long as a condition remains true."}
    ])

    return agent1, agent2, agent3, agent4, agent5



# ==========================================================================================
# ------------------------------------- STACK CREATION -------------------------------------
# ==========================================================================================
def create_stacks(agents: list[BaseAgent]):

    # Stack 1: Education Stack
    stack1 = AgentStack(db_path=Config.DATABASE, name="Education Stack", description="Stack for educational AI agents")
    stack1.create()

    # Stack 2: Support Stack
    stack2 = AgentStack(db_path=Config.DATABASE, name="Support Stack", description="Stack for support AI agents")
    stack2.create()

    # Adding agents to respective stacks
    stack1.add_slot(bot=agents[0]) # MathTutor
    stack1.add_slot(bot=agents[1]) # EnglishTutor
    stack1.add_slot(bot=agents[2]) # ScienceExplainer

    stack2.add_slot(bot=agents[3]) # HistoryBuff
    stack2.add_slot(bot=agents[4]) # CodeHelper


    # Create Checkpoints with Conversations

def create_checkpoints(agent: BaseAgent, versions, conversations):
    for version, convo in zip(versions, conversations):

        # Simulate conversation
        for user_input in convo:
            agent.generate_response(user_input) # By default, generating a response does not create a checkpoint. You can override this behavior using the create_checkpoint=True
        
        # Update system prompt
        agent.system_prompt += f" [Update: {version}]"
        agent.save_to_db(status=f"Checkpoint {version}")  # Since we are updating the system prompt first, we use the checkpoint saving method instead.
        print(f"Checkpoint '{version}' created for agent '{agent.name}'.")

   



# Step 6: Display Tables
def display_table(cursor=None, table_name=None):

    # Connect to the database
    db_connection = sqlite3.connect(Config.DATABASE)
    cursor = db_connection.cursor()

    # Get table data
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    df = pd.DataFrame(rows, columns=columns)
    print(f"\nTable: {table_name}")
    print(df)

    # Close the database connection
    db_connection.commit()
    cursor.close()
    db_connection.close()
    print("\nDatabase operations completed successfully!")

def run_demo_script():
    """ 
    This script simulates an agent building scenario where we create 5 specialized agents
    and assign them to their use-case specific stacks.
    """

    # Initialize the database
    init_database()
    print("Database initialized successfully!")

    # Creating 5 agents ( Each with own prompt, dataset, and memory )
    agent1, agent2, agent3, agent4, agent5 = create_agents()

    agents = [agent1, agent2, agent3, agent4, agent5]

    # Start sessions ( This creates a new save for your bot. This will also load any datasets and memories into the bot's context window )
    for agent in agents:
        agent.start_session(status="initial save")

    # Custom function that creates stacks
    create_stacks(agents=agents)


    # Get example conversations ( convos imported from scripts/conversations/convos_for_demo_script.py )
    conversations = get_conversations()

    # Example conversations for each agent 
    for agent, convo in zip(agents, conversations):
        create_checkpoints(agent, ["v1.1", "v1.2", "v1.3"], convo)

    # End sessions
    for agent in agents:
        agent.end_session()

    # Display tables
    tables_to_display = ['Bots', 'Checkpoints', 'Stacks', 'StackSlots']
    for table in tables_to_display:
        display_table(table_name=table)

