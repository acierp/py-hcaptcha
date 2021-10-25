from .base import Agent
from .chrome import ChromeAgent
from random import choice

def random_agent():
    agent_types = (ChromeAgent,)
    agent_type = choice(agent_types)
    agent = agent_type()
    return agent