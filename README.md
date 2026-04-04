## What This App Does

A reliability-hardened URL shortener API.

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Returns app + DB status. Returns 503 if DB is unreachable. |
| `/shorten` | POST | Accepts `{"url": "https://..."}`, returns a short code. |
| `/r/<code>` | GET | Redirects to the original URL (302), or 410 if deactivated. |
| `/links/<id>` | DELETE | Soft-deactivates a link. |

## Running Tests

No database required — tests use SQLite in-memory.
```bash
uv run pytest tests/ -v
```

With coverage report:
```bash
uv run pytest tests/ --cov=app --cov-report=term-missing -v
```

## Running the App Locally
```bash
# 1. Start the database
docker compose up -d db

# 2. Create tables (run once)
uv run python -c "
from app.database import db
from app.models.link import Link
from peewee import PostgresqlDatabase

db.initialize(PostgresqlDatabase(
    'hackathon_db',
    user='postgres',
    password='postgres',
    host='localhost',
    port=5432
))
db.connect()
db.create_tables([Link])
db.close()
print('Tables created.')
"

# 3. Run the app
uv run run.py

# 4. Verify
curl http://localhost:5000/health
```

## Running in Production (Docker)
```bash
docker compose up --build
```

The app container has `restart: always` — if the process crashes, Docker restarts it automatically.

## CI

GitHub Actions runs the full test suite on every push. Deploys are blocked if any test fails or coverage drops below 70%.