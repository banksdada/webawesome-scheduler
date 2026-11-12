# WebAwesome Scheduler

Job management for cleaning and pest-control businesses. FastAPI (Python) API + Next.js website.

## What works today

| Feature | Status |
|---|---|
| Login (token) | Working, **demo only** - see "Before real use" |
| Customers (add, view, list) | Working |
| Jobs (add, view, list) | Working |
| Quotes (HTML preview) | Working; PDF download is a stub |
| Website | Starter page only (shows whether the API is reachable) |
| Invoicing, calendar, technicians, live updates | **Not built yet** (switched off) |

## Run on your computer

```bash
cp .env.template .env
docker compose up --build
# API: http://localhost:8000/docs     Website: http://localhost:3000
```

## Deploy on Coolify

Create **two** applications from this GitHub repo (one for the API, one for the website). For each:

| Setting | API | Website |
|---|---|---|
| Build pack | Dockerfile | Dockerfile |
| Base directory | `/` | `/` |
| Dockerfile location | `/packages/api/Dockerfile` | `/packages/ui/Dockerfile` |
| Port | `8000` | `3000` |

Environment variables:
- **API:** `SECRET_KEY` (long random text), `DATABASE_URL` (a Coolify PostgreSQL database), `CORS_ORIGINS` (the website's address, e.g. `https://scheduler.yourdomain.com`).
- **Website:** `NEXT_PUBLIC_API_URL` = the API's address. Tick **Build Variable** for it - the website is built with this value, so changing it needs a redeploy.

Health check: `GET /health` on the API returns `{"status":"ok"}`.

## Before real use

- Login accepts the password `password` for any existing user, and there is no sign-up screen yet. Replace this with real password hashing before putting real customer data in.
- The default database is a file inside the container. Use PostgreSQL in Coolify.

## Tests

```bash
pip install -r packages/api/requirements.txt pytest httpx ruff
cd packages && python -m pytest api/tests -q
```
