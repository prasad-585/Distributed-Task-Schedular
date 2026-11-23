# Distributed Task Scheduling Engine

Portfolio learning project using FastAPI, SQLModel, PostgreSQL, Redis, JWT, a scheduler process, and worker process.

## Features
- Register/login with JWT
- User-owned task create/list/detail/update/cancel
- Scheduled and recurring demo tasks
- Redis sorted-set priority queue (priority 1 is highest)
- Per-user Redis rate limit (100 requests/minute on task creation)
- Task logs and dead-letter records
- Separate scheduler and worker processes
- Docker Compose local setup
- Render Blueprint (`render.yaml`) starter deployment configuration

## Run locally (Python + local Redis)
1. Create a virtual environment and install requirements.
2. Copy `.env.example` to `.env` and set values.
3. Start Redis locally.
4. Run API: `uvicorn app.main:app --reload`
5. Run scheduler in another terminal: `python -m app.services.scheduler`
6. Run worker in another terminal: `python -m app.services.worker`

## Run with Docker Compose
```powershell
docker compose up --build
```
API: http://localhost:8000/docs

## Register and login
POST `/auth/register`
```json
{"email":"demo@example.com","password":"StrongPass123"}
```
POST `/auth/login`
```json
{"email":"demo@example.com","password":"StrongPass123"}
```
Copy `access_token`, click Authorize in Swagger, and enter `Bearer YOUR_TOKEN`.

## Create task
POST `/tasks`
```json
{
  "name":"My first scheduled task",
  "task_type":"demo",
  "payload":{"message":"hello"},
  "scheduled_at":"2026-11-17T10:00:00+00:00",
  "priority":1,
  "max_retries":3
}
```
For immediate execution, use a timestamp in the past or omit `scheduled_at`.
Recurring example: set `interval_seconds` to `60`.

## Important learning limitations
This is an educational starter, not production-grade distributed infrastructure:
- Redis `ZPOPMIN` removes before acknowledgement; a worker crash can lose a queued item.
- Scheduler enqueue and database update are not transactionally coupled (outbox pattern is a production improvement).
- Task claim is basic; stronger atomic DB claim/lease/heartbeat recovery is needed.
- `create_all` is used for convenience; use Alembic migrations for production.
- Demo task handler prints payload; it does not send email or perform payments.
- Render free services may sleep/expire and may not support always-on background workers.
- Use unique secrets, TLS, backups, and paid always-on services for real deployments.
