# conftest.py
import pytest
from peewee import SqliteDatabase
from app import create_app
from app.models.link import Link

_MODELS = [Link]


@pytest.fixture(scope="function")
def app():
    from app.database import db

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    test_db = SqliteDatabase(":memory:", pragmas={"foreign_keys": 1})
    db.initialize(test_db)

    # Hold the connection open for the entire test.
    # In-memory SQLite is destroyed when its connection closes,
    # so we must prevent the before_request/teardown hooks from
    # opening and closing a fresh connection on each request.
    test_db.connect()
    test_db.create_tables(_MODELS)

    # Patch the hooks so Flask doesn't close/reopen the connection mid-test
    flask_app.before_request_funcs[None] = []
    flask_app.teardown_appcontext_funcs = []

    yield flask_app

    test_db.drop_tables(_MODELS)
    test_db.close()


@pytest.fixture
def client(app):
    return app.test_client()