from ui import run_tui, AgentEvent
from memory import Memory
from agent import Agent
import config

memory = Memory()
agent = Agent(memory)

def agent_runner(user_message: str, emit_fn):
    agent.run(user_message, emit_fn=emit_fn)

if __name__ == "__main__":
    run_tui(agent_runner)

def run():
    run_tui(agent_runner)