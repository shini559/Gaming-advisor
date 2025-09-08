from classes.agent_manager import AgentManager
from classes.interface_manager import InterfaceManager
from classes.settings import Settings


if __name__ == "__main__":

    settings = Settings()
    tools = []
    agent_executor = AgentManager().initialize(settings, tools).executor
    InterfaceManager().initialize(settings, agent_executor)