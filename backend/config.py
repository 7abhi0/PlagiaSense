import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class loading from environment variables"""
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/plagiasense")
    JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
    MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(os.path.dirname(__file__), "models", "model.pkl"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
