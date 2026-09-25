import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    playwright_token = os.getenv("PLAYWRIGHT_MCP_TOKEN")
    openai_model = os.getenv("OPENAI_MODEL")

def get_settings():
    return Settings()


settings = get_settings()

