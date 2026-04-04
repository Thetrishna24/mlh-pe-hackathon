# routes/health.py
# Why does health check the DB? Load balancers ping /health to decide if
# this instance should receive traffic. A Flask process that can't reach
# its DB is not healthy — returning 200 would be lying to the LB.
from flask import Blueprint, jsonify
from app.database import db

import time

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    try:
        # Cheapest possible DB round-trip — no table scan
        db.execute_sql("SELECT 1")
        db_status = "ok"
        start = time.monotonic()
        db.execute_sql("SELECT 1")
        latency_ms = round((time.monotonic() - start) * 1000, 2)
    except Exception as e:
        # Log the real error server-side, return sanitized message to client
        print(f"[HEALTH] DB check failed: {e}")
        db_status = "degraded"

    status = "ok" if db_status == "ok" else "degraded"
    http_code = 200 if status == "ok" else 503

    return jsonify({"status": "ok", "db": "ok", "db_latency_ms": latency_ms, "version": "1.0.0"}), http_code