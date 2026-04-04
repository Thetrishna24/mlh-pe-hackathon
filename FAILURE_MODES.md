# Failure Modes & Recovery Runbook

## FM-1: Database Unreachable

**Symptom:** `GET /health` returns `{"status": "degraded", "db": "degraded"}` with HTTP 503.

**Cause:** PostgreSQL container is down, network partition, or credentials changed.

**Impact:** All `/shorten` and `/r/<code>` requests will fail with 500.

**Recovery:**
```bash
docker compose ps          # check if db container is running
docker compose restart db  # restart DB
curl http://localhost:5000/health  # confirm recovery
```

---

## FM-2: App Container Crashes

**Symptom:** No response on port 5000.

**Cause:** Unhandled exception, OOM kill, or manual `docker kill`.

**Recovery:** Automatic. `restart: always` in docker-compose means Docker restarts the container within seconds. Verify:
```bash
docker compose ps          # should show app as "Up"
docker compose logs app    # inspect crash reason
```

---

## FM-3: Duplicate Short Code (Race Condition)

**Symptom:** `POST /shorten` returns HTTP 409.

**Cause:** Astronomically rare — two concurrent requests generated the same code and hit the DB unique constraint simultaneously.

**Impact:** Single request fails. Retry is safe — client can re-POST.

**Recovery:** Client retries the request. Server-side: `generate_code()` retries up to 5 times before raising.

---

## FM-4: Bad Input / Malformed Request

**Symptom:** HTTP 400 with JSON error message.

**Cause:** Client sent invalid JSON, a disallowed URL scheme, or an empty URL.

**Impact:** None — request is rejected before touching the DB.

**Recovery:** No server action needed. Client fixes their request.

---

## FM-5: Deactivated Link Accessed

**Symptom:** `GET /r/<code>` returns HTTP 410 Gone.

**Cause:** Link was soft-deleted via `DELETE /links/<id>`.

**Impact:** Expected behavior — not an error condition.

**Recovery:** N/A. 410 is intentional and semantically distinct from 404.