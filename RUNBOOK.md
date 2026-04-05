# 🚨 Operations Runbook: MLH-PE-Hackathon API

This document provides step-by-step instructions for responding to system alerts. 

---

## 🛠 Quick Diagnostics
If you are paged, start here:
1. **Check Health Endpoint:** `curl http://localhost:5000/health`
   - Look for `db_latency_ms`. If > 500ms, the database is struggling.
2. **Check Logs:** Search for `{"level": "ERROR"}` in the log stream.
3. **Verify Tests:** Run `uv run pytest` to ensure core logic is still intact.

---

## 🔥 Common Incident Scenarios

### 1. Database Connection Failures
**Symptom:** Logs show `PeeweeException` or `/health` returns `db: "error"`.
**Action:**
* Verify `DATABASE_URL` environment variable is correct.
* Check if the PostgreSQL instance is reachable: `pg_isready -h [host]`.
* Restart the application to refresh the connection pool.

### 2. High Rate Limit Triggers (429 Errors)
**Symptom:** Users reporting "Rate limit exceeded" unexpectedly.
**Action:**
* Check logs for `Remote Address` patterns. If it's a single IP, it's a bot/scraper.
* To temporarily adjust limits, update `DEFAULT_LIMITS` in `app/__init__.py`.
* Check if `get_remote_address` is correctly identifying users (especially if behind a proxy like Nginx).

### 3. Short Code Collisions
**Symptom:** Logs show `IntegrityError` or `Collision detected` warnings during `/shorten`.
**Action:**
* The 6-8 character entropy might be exhausted for the current user base.
* **Hotfix:** Manually increase the length in `Link.generate_code()` in `app/models/link.py`.

### 4. Application Slowdown (Latency)
**Symptom:** `db_latency_ms` is high.
**Action:**
* Check for long-running queries in Postgres: `SELECT * FROM pg_stat_activity;`.
* Verify if the `Link.url` or `Link.code` columns have lost their indexes.

---

## 🚀 Deployment / Recovery
* **Restart App:** `uv run run.py`
* **Clear Cache/DB:** (Use only in extreme cases) `DROP TABLE link;` and restart to let Peewee recreate schemas.