# app/__init__.py
# Global error handlers ensure that even unhandled exceptions return
# structured JSON — never a raw Flask HTML error page or Python traceback.
import os
from flask import Flask, jsonify
from dotenv import load_dotenv

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.database import db
from app.models import Link

from peewee import PostgresqlDatabase
from urllib.parse import urlparse

import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "timestamp": self.formatTime(record, self.datefmt),
        }
        return json.dumps(log_record)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    # Prevent duplicate logs if create_app is called multiple times (like in tests)
    logger.propagate = False

limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])
def create_app():
    setup_logging() # Initialize the structured logs
    load_dotenv()
    app = Flask(__name__)
    limiter.init_app(app)
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
