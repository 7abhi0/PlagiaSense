import os
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient


def init_extensions(app):
    # CORS
    CORS(app, resources={"/*": {"origins": os.getenv('CORS_ORIGINS', '*')}})
    # JWT
    jwt = JWTManager(app)
    # Rate Limiter
    limiter = Limiter(app, key_func=get_remote_address, default_limits=["100 per hour"])
    # MongoDB
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/plagiasense')
    client = MongoClient(mongo_uri)
    app.db = client.get_default_database()
    # expose extensions for import convenience
    app.extensions = getattr(app, 'extensions', {})
    app.extensions['jwt'] = jwt
    app.extensions['limiter'] = limiter
    app.extensions['mongo'] = client
    return app
