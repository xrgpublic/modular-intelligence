from modular_intelligence.stack.stack import AgentStack
from modular_intelligence.database.config import Config

stack = AgentStack(db_path=Config.DATABASE)
stack.load_from_db(stack_id=1)

print("agents", stack.agents)