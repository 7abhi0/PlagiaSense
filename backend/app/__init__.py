import os
from flask import Flask
from .config import Config
from .extensions import init_extensions
from .middleware import register_error_handlers

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/", methods=["GET"])
    def health_root():
        return {"status": "ok", "message": "PlagiaSense API is running"}, 200
    
    upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    init_extensions(app)
    
    from .routes.auth import auth_bp
    from .routes.scan import scan_bp
    from .routes.report import report_bp
    from .routes.admin import admin_bp
    from .routes.health import health_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(scan_bp, url_prefix='/api/scan')
    app.register_blueprint(report_bp, url_prefix='/api/reports')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    register_error_handlers(app)
    return app
