"""End-to-end smoke test: health, login, customer, job and quote."""
import os
import tempfile

# Use a throw-away database, set BEFORE the app is imported.
_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_db.name}"
os.environ["SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

from api.main import app, engine  # noqa: E402
from api import models  # noqa: E402


def test_health_and_full_flow():
    with TestClient(app) as client:  # runs start-up, creates tables
        assert client.get("/health").json()["status"] == "ok"

        # protected routes need a login
        assert client.get("/customers").status_code == 401

        with Session(engine) as s:
            s.add(models.User(email="boss@example.com", password="x"))
            s.commit()

        tok = client.post("/token", data={"username": "boss@example.com", "password": "password"})
        assert tok.status_code == 200
        auth = {"Authorization": f"Bearer {tok.json()['access_token']}"}

        cust = client.post("/customers", json={"name": "Acme Cleaning"}, headers=auth)
        assert cust.status_code == 200, cust.text
        cid = cust.json()["id"]

        body = {"title": "Deep clean", "customer_id": cid, "price_estimate": 120}
        job = client.post("/jobs", json=body, headers=auth)
        assert job.status_code == 200, job.text
        jid = job.json()["id"]

        assert len(client.get("/jobs", headers=auth).json()) == 1
        quote = client.post(f"/quotes/generate?job_id={jid}", headers=auth)
        assert quote.status_code == 200, quote.text
        assert "Acme Cleaning" in quote.json()["html"]


def test_switched_on_but_missing_feature_does_not_crash():
    # invoicing has no code yet; switching it on must just log a warning, not crash
    import api.main as m

    m.include_optional(True, "invoicing", "/invoices")
