# app/__init__.py
# Global error handlers ensure that even unhandled exceptions return
# structured JSON — never a raw Flask HTML error page or Python traceback.
import os
from flask import Flask, jsonify
from dotenv import load_dotenv

from app.database import db
from app.models import Link

from peewee import PostgresqlDatabase
from urllib.parse import urlparse

def create_app():
    load_dotenv()
    app = Flask(__name__)

    database_url = os.getenv("DATABASE_URL", "postgresql://localhost/hackathon_db")
    parsed = urlparse(database_url)
    db.initialize(PostgresqlDatabase(
        database=parsed.path[1:],  # Remove leading '/'
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port or 5432
    ))

    from app.routes import register_routes
    register_routes(app)

    @app.before_request
    def open_connection():
        if db.is_closed():
            db.connect()

    @app.teardown_appcontext
    def close_connection(exc):
        if not db.is_closed():
            db.close()

    # --- Global error handlers (Gold: graceful failure) ---

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        # Log real error server-side; return sanitized message to client
        app.logger.error(f"Internal error: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

    return app
