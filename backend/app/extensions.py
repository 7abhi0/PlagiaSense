import os
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from pymongo import MongoClient

# Global extension instances (initialized later via init_extensions)
cors = CORS()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)
db = None  # MongoDB database reference, set in init_extensions


def init_extensions(app):
    """Initialize all Flask extensions with the given app instance.
    Must be called from the app factory after app.config is loaded.
    """
    # CORS – allow origins from env var (defaults to * for local dev)
    cors.init_app(
        app,
        resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}},
        supports_credentials=True,
    )

    # JWT
    jwt.init_app(app)
    app.extensions["jwt"] = jwt

    # Rate limiting – only call init_app (key_func already set above)
    limiter.init_app(app)
    app.extensions["limiter"] = limiter

    # MongoDB
    mongo_uri = app.config.get("MONGO_URI", "mongodb://localhost:27017/plagiasense")
    mongo_client = MongoClient(mongo_uri)
    global db
    db = mongo_client.get_default_database() if "mongodb+srv" in mongo_uri or "/" in mongo_uri.split("@")[-1] else mongo_client["plagiasense"]
    app.extensions["mongo"] = mongo_client
    app.extensions["db"] = db
    return app
