def register_error_handlers(app):
    @app.errorhandler(400)
    def handle_400(error):
        return {"error": "Bad Request", "message": str(error)}, 400

    @app.errorhandler(401)
    def handle_401(error):
        return {"error": "Unauthorized", "message": str(error)}, 401

    @app.errorhandler(404)
    def handle_404(error):
        return {"error": "Not Found", "message": str(error)}, 404

    @app.errorhandler(429)
    def handle_429(error):
        return {"error": "Too Many Requests", "message": str(error)}, 429

    @app.errorhandler(Exception)
    def handle_exception(error):
        import traceback
        traceback.print_exc()
        return {"error": "Internal Server Error", "message": str(error)}, 500
