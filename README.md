# WebAwesome Scheduler - Job Scheduling & Dispatch

Book jobs, assign them to technicians, see the week on a calendar, and let technicians work their jobs from a phone.
FastAPI (Python) API + Next.js website.

## What it does

| | |
|---|---|
| **Accounts** | A business signs up and becomes its own private workspace. Roles: **admin** (office) and **technician**. Passwords are hashed. |
| **Customers** | Admin adds customers (name, phone, address, notes). |
| **Jobs** | Admin creates a job for a customer with a date/time and length. |
| **Dispatch** | Admin assigns a technician. A clash warning appears if that technician is already booked (admin can still save anyway). The technician is **emailed** when a job is assigned or its time changes. |
| **Week calendar** | Admin sees the week, can filter by technician, and sees jobs that still need a time. |
| **Technician phone view** | "My jobs": only their own jobs, with call and Maps links, and **Start job** / **Mark as done** buttons. |
| **Quotes** | Admin can open a simple printable quote for a job. |

One business can never see another business's data (this is tested).

## Not built yet

SMS notifications, invoicing and payments, recurring jobs, route maps, password reset, email verification, customer-facing booking, and billing for your own subscribers. Login has no rate limiting yet.

## Run on your computer

```bash
cp .env.template .env
docker compose up --build
# Website: http://localhost:3000     API docs: http://localhost:8000/docs
```

## Deploy on Coolify

Create a **PostgreSQL database** and **two applications** from this GitHub repo (branch `main`):

| Setting | API | Website |
|---|---|---|
| Build pack | Dockerfile | Dockerfile |
| Base directory | `/` | `/` |
| Dockerfile location | `/packages/api/Dockerfile` | `/packages/ui/Dockerfile` |
| Port | `8000` | `3000` |

**API variables:** `SECRET_KEY` (long random text), `DATABASE_URL` (the database's internal URL), `CORS_ORIGINS` (the website's address, e.g. `https://scheduler.yourdomain.com`), and optionally the `SMTP_*` email settings.

**Website variable:** `NEXT_PUBLIC_API_URL` = the API's address. Tick **Build Variable** - the website is built with this value, so changing it needs a redeploy.

Health check: `GET /health` on the API returns `{"status":"ok"}`.

## Tests

```bash
pip install -r packages/api/requirements.txt pytest httpx ruff
cd packages && python -m pytest api/tests -q
```
