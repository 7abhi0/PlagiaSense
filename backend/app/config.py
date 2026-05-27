import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Flask configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'jwt-secret-key')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
    FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    FIREBASE_APP_NAME = os.getenv('FIREBASE_APP_NAME', 'plagiasense-backend')
    # Rate limiting defaults are set in extensions.py
    # Model path for AI detection
    MODEL_PATH = os.getenv('MODEL_PATH', os.path.join(os.path.dirname(__file__), '..', 'models', 'model.pkl'))
    # TF-IDF reference corpus path
    REFERENCE_CORPUS = os.getenv('REFERENCE_CORPUS', os.path.join(os.path.dirname(__file__), '..', 'datasets', 'reference_corpus.txt'))
