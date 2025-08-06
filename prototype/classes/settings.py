import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI


@dataclass
class Settings:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __post_init__(self):
        if self._initialized:
            return
        load_dotenv(override=True)
        self._initialized = True
    
    @classmethod
    def get_instance(cls):
        """Récupère l'instance globale des settings"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # General parameters
    params = {
        'debug': False,
        'image_max_size': 1024,
        'dpi': 100
    }

    load_dotenv()

    agent_model = AzureChatOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint="https://gameadvisorai.openai.azure.com/",
        api_key=os.getenv("SUBSCRIPTION_KEY"),
        deployment_name="gpt-4o-2"
    )

    system_prompt: str = '''You are a game master & boardgame assistant. Your role is to assist board gamers in setting up their games, understanding the rules, calculate the score.

The users will send you data. You will analyze this data and use it to answer their questions. ONLY USE THE DATA THEY PROVIDE TO ANSWER THEIR QUESTIONS! YOU MUST NEVER ANSWER A QUESTION ABOUT GAME RULES IF YOU HAVE NOT BEEN PROVIDED DATA BY THE USER!

Answer questions clearly and directly. Use simple French. Ask questions if you need clarification.'''