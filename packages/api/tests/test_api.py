"""End-to-end tests: accounts, roles, privacy between businesses, scheduling, dispatch."""

import os
import tempfile
import uuid

# Throw-away database, set BEFORE the app is imported.
_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_db.name}"
os.environ["SECRET_KEY"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from api import models, notify  # noqa: E402
from api.db import engine  # noqa: E402
from api.main import app  # noqa: E402

PASSWORD = "correct-horse-battery"


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def sent(monkeypatch):
    """Capture emails instead of sending them."""
    box = []
    monkeypatch.setattr(notify, "send_email", lambda to, subject, body: box.append((to, subject, body)) or True)
    return box


def uniq(prefix="u"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def signup(client, org="Acme Cleaning"):
    email = uniq("admin")
    r = client.post("/auth/signup", json={"organisation_name": org, "name": "Boss", "email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return email, {"Authorization": f"Bearer {r.json()['access_token']}"}


def login(client, email, password=PASSWORD):
    r = client.post("/token", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def add_tech(client, admin, name="Tom Tech"):
    email = uniq("tech")
    r = client.post("/team", json={"name": name, "email": email, "password": PASSWORD, "phone": "07000 000000"}, headers=admin)
    assert r.status_code == 200, r.text
    return r.json()["id"], email


def add_customer(client, admin, name="Mrs Smith", address="1 High Street"):
    r = client.post("/customers", json={"name": name, "address": address, "phone": "01234 567890"}, headers=admin)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def add_job(client, admin, cid, tech=None, start="2030-06-03T10:00:00Z", minutes=60, **extra):
    body = {"customer_id": cid, "title": "Deep clean", "scheduled_start": start, "duration_minutes": minutes, **extra}
    if tech:
        body["assigned_to_id"] = tech
    return client.post("/jobs", json=body, headers=admin)


# ------------------------------------------------------------------ accounts
def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_signup_login_and_password_is_hashed(client):
    email, admin = signup(client)
    me = client.get("/me", headers=admin).json()
    assert me["role"] == "admin" and me["email"] == email

    with Session(engine) as s:
        user = s.exec(select(models.User).where(models.User.email == email)).one()
        assert user.password_hash != PASSWORD and user.password_hash.startswith("$2")

    assert client.post("/token", data={"username": email, "password": "wrong-password"}).status_code == 400
    assert client.post("/token", data={"username": email, "password": "password"}).status_code == 400  # old demo password
    login(client, email.upper())  # emails are not case sensitive


def test_signup_rules(client):
    email, _ = signup(client)
    dup = client.post("/auth/signup", json={"organisation_name": "X", "name": "Y", "email": email, "password": PASSWORD})
    assert dup.status_code == 409
    short = client.post("/auth/signup", json={"organisation_name": "X", "name": "Y", "email": uniq(), "password": "short"})
    assert short.status_code == 422
    assert client.get("/customers").status_code == 401
    assert client.get("/jobs", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_technician_has_limited_powers(client):
    _, admin = signup(client)
    _, tech_email = add_tech(client, admin)
    tech = login(client, tech_email)
    cid = add_customer(client, admin)
    assert client.get("/team", headers=tech).status_code == 403
    assert client.get("/customers", headers=tech).status_code == 403
    assert client.post("/customers", json={"name": "x"}, headers=tech).status_code == 403
    assert add_job(client, tech, cid).status_code == 403
    assert client.get("/me", headers=tech).json()["role"] == "technician"


def test_deactivated_user_is_locked_out(client):
    _, admin = signup(client)
    tid, tech_email = add_tech(client, admin)
    tech = login(client, tech_email)
    assert client.patch(f"/team/{tid}", json={"active": False}, headers=admin).status_code == 200
    assert client.get("/me", headers=tech).status_code == 401
    assert client.post("/token", data={"username": tech_email, "password": PASSWORD}).status_code == 400


# ------------------------------------------------------------------ privacy between businesses
def test_one_business_cannot_see_another(client):
    _, a = signup(client, "Business A")
    _, b = signup(client, "Business B")
    a_tech, _ = add_tech(client, a)
    a_cust = add_customer(client, a)
    a_job = add_job(client, a, a_cust, a_tech).json()["id"]

    assert client.get("/customers", headers=b).json() == []
    assert client.get(f"/customers/{a_cust}", headers=b).status_code == 404
    assert client.patch(f"/customers/{a_cust}", json={"name": "Hacked"}, headers=b).status_code == 404
    assert client.get("/jobs", headers=b).json() == []
    assert client.get(f"/jobs/{a_job}", headers=b).status_code == 404
    assert client.patch(f"/jobs/{a_job}", json={"title": "Hacked"}, headers=b).status_code == 404
    assert client.post(f"/quotes/generate?job_id={a_job}", headers=b).status_code == 404
    assert [u["id"] for u in client.get("/team", headers=b).json()] != [a_tech]
    assert client.patch(f"/team/{a_tech}", json={"active": False}, headers=b).status_code == 404

    b_cust = add_customer(client, b, "B customer")
    assert add_job(client, b, a_cust).status_code == 404  # B's job on A's customer
    assert add_job(client, b, b_cust, a_tech).status_code == 404  # B assigning A's technician


# ------------------------------------------------------------------ dispatch
def test_assign_notify_and_work_a_job(client, sent):
    _, admin = signup(client)
    tid, tech_email = add_tech(client, admin)
    other_id, other_email = add_tech(client, admin, "Other Tech")
    cid = add_customer(client, admin)

    created = add_job(client, admin, cid, tid, notes="Key under the mat")
    assert created.status_code == 200, created.text
    job = created.json()
    assert job["status"] == "assigned"
    assert job["assigned_to"]["name"] == "Tom Tech" and job["customer"]["address"] == "1 High Street"
    assert job["scheduled_start"].endswith("Z")

    # the technician was emailed, with the job details
    assert len(sent) == 1 and sent[0][0] == tech_email
    assert "Deep clean" in sent[0][1] and "1 High Street" in sent[0][2] and "Key under the mat" in sent[0][2]

    tech, other = login(client, tech_email), login(client, other_email)
    assert [j["id"] for j in client.get("/jobs", headers=tech).json()] == [job["id"]]
    assert client.get("/jobs", headers=other).json() == []
    assert client.get(f"/jobs/{job['id']}", headers=other).status_code == 404
    assert client.post(f"/jobs/{job['id']}/start", headers=other).status_code == 404

    started = client.post(f"/jobs/{job['id']}/start", headers=tech)
    assert started.status_code == 200 and started.json()["status"] == "in_progress" and started.json()["started_at"]
    assert client.post(f"/jobs/{job['id']}/start", headers=tech).status_code == 409
    done = client.post(f"/jobs/{job['id']}/complete", headers=tech)
    assert done.status_code == 200 and done.json()["status"] == "done" and done.json()["completed_at"]
    assert client.post(f"/jobs/{job['id']}/complete", headers=tech).status_code == 409
    # a finished job cannot be moved around
    assert client.patch(f"/jobs/{job['id']}", json={"assigned_to_id": other_id}, headers=admin).status_code == 409


def test_unassigned_job_cannot_be_started(client):
    _, admin = signup(client)
    cid = add_customer(client, admin)
    job = add_job(client, admin, cid).json()
    assert job["status"] == "pending" and job["assigned_to"] is None
    assert client.post(f"/jobs/{job['id']}/start", headers=admin).status_code == 409


def test_clash_detection(client):
    _, admin = signup(client)
    tid, _ = add_tech(client, admin)
    t2, _ = add_tech(client, admin, "Second Tech")
    cid = add_customer(client, admin)

    first = add_job(client, admin, cid, tid, "2030-06-03T10:00:00Z", 60).json()
    clash = add_job(client, admin, cid, tid, "2030-06-03T10:30:00Z", 60)
    assert clash.status_code == 409
    assert clash.json()["detail"]["conflicts"][0]["id"] == first["id"]

    assert add_job(client, admin, cid, tid, "2030-06-03T11:00:00Z", 60).status_code == 200  # back-to-back is fine
    assert add_job(client, admin, cid, t2, "2030-06-03T10:30:00Z", 60).status_code == 200  # different technician
    assert add_job(client, admin, cid, tid, "2030-06-03T10:30:00Z", 30, allow_overlap=True).status_code == 200  # forced

    # moving a job onto a busy slot is also caught
    free = add_job(client, admin, cid, tid, "2030-06-04T09:00:00Z", 60).json()
    move = client.patch(f"/jobs/{free['id']}", json={"scheduled_start": "2030-06-03T10:15:00Z"}, headers=admin)
    assert move.status_code == 409

    # starting exactly when the 11:00-12:00 job ends is fine
    body = {"scheduled_start": "2030-06-03T12:00:00Z", "duration_minutes": 30}
    assert client.patch(f"/jobs/{free['id']}", json=body, headers=admin).status_code == 200


def test_cancelled_job_frees_the_slot(client):
    _, admin = signup(client)
    tid, _ = add_tech(client, admin)
    cid = add_customer(client, admin)
    job = add_job(client, admin, cid, tid, "2030-06-03T10:00:00Z", 60).json()
    assert add_job(client, admin, cid, tid, "2030-06-03T10:30:00Z", 60).status_code == 409
    assert client.patch(f"/jobs/{job['id']}", json={"status": "cancelled"}, headers=admin).json()["status"] == "cancelled"
    assert add_job(client, admin, cid, tid, "2030-06-03T10:30:00Z", 60).status_code == 200


def test_reassign_unassign_and_reschedule_send_email(client, sent):
    _, admin = signup(client)
    t1, t1_email = add_tech(client, admin)
    t2, t2_email = add_tech(client, admin, "Second Tech")
    cid = add_customer(client, admin)
    job = add_job(client, admin, cid).json()  # no technician -> no email
    assert sent == []

    r = client.patch(f"/jobs/{job['id']}", json={"assigned_to_id": t1}, headers=admin)
    assert r.json()["status"] == "assigned" and [m[0] for m in sent] == [t1_email]

    client.patch(f"/jobs/{job['id']}", json={"assigned_to_id": t2}, headers=admin)  # reassigned
    assert sent[-1][0] == t2_email

    client.patch(f"/jobs/{job['id']}", json={"scheduled_start": "2030-06-05T14:00:00Z"}, headers=admin)  # new time
    assert len(sent) == 3 and sent[-1][0] == t2_email

    client.patch(f"/jobs/{job['id']}", json={"title": "Renamed"}, headers=admin)  # not a schedule change
    assert len(sent) == 3

    r = client.patch(f"/jobs/{job['id']}", json={"assigned_to_id": None}, headers=admin)  # unassign
    assert r.json()["status"] == "pending" and r.json()["assigned_to"] is None


# ------------------------------------------------------------------ calendar listing
def test_week_view_filters_and_timezones(client):
    _, admin = signup(client)
    tid, _ = add_tech(client, admin)
    cid = add_customer(client, admin)
    add_job(client, admin, cid, tid, "2030-06-03T10:00:00Z")
    add_job(client, admin, cid, tid, "2030-06-05T10:00:00Z")
    add_job(client, admin, cid, tid, "2030-06-12T10:00:00Z")
    unscheduled = client.post("/jobs", json={"customer_id": cid, "title": "No time yet"}, headers=admin).json()

    week = client.get("/jobs", params={"start": "2030-06-03T00:00:00Z", "end": "2030-06-10T00:00:00Z"}, headers=admin).json()
    assert [j["scheduled_start"] for j in week] == ["2030-06-03T10:00:00Z", "2030-06-05T10:00:00Z"]

    todo = client.get("/jobs", params={"unscheduled": "true"}, headers=admin).json()
    assert [j["id"] for j in todo] == [unscheduled["id"]]

    # a time sent with a UK summer offset is stored as UTC
    r = add_job(client, admin, cid, None, "2030-07-01T10:00:00+01:00").json()
    assert r["scheduled_start"] == "2030-07-01T09:00:00Z"


# ------------------------------------------------------------------ quotes
def test_quote_escapes_html(client):
    _, admin = signup(client, "Org <b>x</b>")
    cid = add_customer(client, admin, name="<script>alert(1)</script>")
    job = add_job(client, admin, cid, price_estimate=120).json()
    html = client.post(f"/quotes/generate?job_id={job['id']}", headers=admin).json()["html"]
    assert "<script>" not in html and "&lt;script&gt;" in html and "120.00" in html


def test_missing_email_settings_never_break_scheduling(client):
    # without SMTP_HOST the real send_email just logs and returns False
    assert notify.send_email("a@example.com", "hi", "body") is False
