import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    MONGO_URI: str = os.getenv("MONGO_URI")
    PUBMED_API_KEY: str = os.getenv("PUBMED_API_KEY")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

settings = Settings()