import os
from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr
from pydantic_settings import SettingsConfigDict,BaseSettings

class SecretKeys(BaseSettings):

    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8')
    GROQ_API_KEY:SecretStr
    # AVIATIONSTACK_API_KEY:SecretStr
    # TAVILY_API_KEY:SecretStr
    # LANGSMITH_API_KEY:SecretStr
    # ANTHROPIC_API_KEY:SecretStr


secret_keys = SecretKeys()

#TODO fix this bug

    