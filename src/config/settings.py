import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("travel_agent_system")

class Settings:
    # Weather
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    # Email
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    # Database
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT","5432")
    
    # AWS / Bedrock
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-7-sonnet-20250219-v1:0")

settings = Settings()