import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Flask configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'jwt-secret-key')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/plagiasense')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    # Rate limiting defaults are set in extensions.py
    # Model path for AI detection
    MODEL_PATH = os.getenv('MODEL_PATH', os.path.join(os.path.dirname(__file__), '..', 'models', 'model.pkl'))
    # TF-IDF reference corpus path
    REFERENCE_CORPUS = os.getenv('REFERENCE_CORPUS', os.path.join(os.path.dirname(__file__), '..', 'datasets', 'reference_corpus.txt'))
