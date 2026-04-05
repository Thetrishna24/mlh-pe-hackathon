# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv --no-cache-dir

COPY pyproject.toml .
COPY uv.lock* .
RUN uv sync --no-dev

COPY . .

# Expose app port
EXPOSE 5000

# Gunicorn for production — not Flask dev server
CMD ["uv", "run", "gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "run:app"]