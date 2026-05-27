import os

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .firestore_adapter import initialize_firestore

cors = CORS()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)
db = None


def init_extensions(app):
    cors_origins = os.getenv("CORS_ORIGINS")
    if cors_origins:
        # Support comma-separated list in env var
        origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    else:
        origins = ["https://plagia-sense.vercel.app"]

    cors.init_app(
        app,
        resources={r"/*": {"origins": origins}},
        supports_credentials=True,
    )

    jwt.init_app(app)
    app.extensions["jwt"] = jwt

    limiter.init_app(app)
    app.extensions["limiter"] = limiter

    global db
    db = initialize_firestore(app)
    app.extensions["db"] = db
    return app
