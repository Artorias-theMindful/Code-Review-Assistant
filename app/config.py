from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4"
    project_name: str = "Code Review Assistant"
    version: str = "1.0.0"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
