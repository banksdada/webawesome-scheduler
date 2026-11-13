"""Password reset: emailed link, one use, one hour, and no hints about who has an account."""

import re
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from . import test_api as t  # sets up the throw-away database before the app loads
from api import models, notify  # noqa: E402
from api.db import engine  # noqa: E402
from api.main import app  # noqa: E402

PASSWORD, signup, add_tech, uniq = t.PASSWORD, t.signup, t.add_tech, t.uniq


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def sent(monkeypatch):
    box = []
    monkeypatch.setattr(notify, "send_email", lambda to, subject, body: box.append((to, subject, body)) or True)
    return box


NEW = "a-brand-new-password"


def token_from(sent_mail):
    return re.search(r"token=([\w-]+)", sent_mail[-1][2]).group(1)


def test_unknown_email_gets_same_answer_and_no_email(client, sent, monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://x.test")
    r = client.post("/auth/forgot", json={"email": uniq("nobody")})
    assert r.status_code == 200 and r.json() == {"ok": True}
    assert sent == []


def test_full_reset_flow_and_single_use(client, sent, monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://x.test")
    email, _ = signup(client)
    assert client.post("/auth/forgot", json={"email": email}).status_code == 200
    assert len(sent) == 1 and sent[0][0] == email and "https://x.test/reset?token=" in sent[0][2]
    token = token_from(sent)

    assert client.post("/auth/reset", json={"token": token, "password": NEW}).status_code == 200
    assert client.post("/token", data={"username": email, "password": PASSWORD}).status_code == 400
    assert client.post("/token", data={"username": email, "password": NEW}).status_code == 200
    # the same link cannot be used twice
    assert client.post("/auth/reset", json={"token": token, "password": "another-password"}).status_code == 400


def test_expired_link_rejected(client, sent, monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://x.test")
    email, _ = signup(client)
    client.post("/auth/forgot", json={"email": email})
    token = token_from(sent)
    with Session(engine) as s:
        for rec in s.exec(select(models.PasswordReset)).all():
            rec.expires_at = models.utcnow() - timedelta(minutes=1)
            s.add(rec)
        s.commit()
    r = client.post("/auth/reset", json={"token": token, "password": NEW})
    assert r.status_code == 400 and "expired" in r.json()["detail"]


def test_bad_inputs_rejected(client, sent, monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://x.test")
    email, _ = signup(client)
    client.post("/auth/forgot", json={"email": email})
    token = token_from(sent)
    assert client.post("/auth/reset", json={"token": token, "password": "short"}).status_code == 422
    assert client.post("/auth/reset", json={"token": "x" * 43, "password": NEW}).status_code == 400
    assert client.post("/auth/forgot", json={"email": "not-an-email"}).status_code == 422


def test_limited_to_three_emails_an_hour(client, sent, monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://x.test")
    email, _ = signup(client)
    for _ in range(5):
        assert client.post("/auth/forgot", json={"email": email}).status_code == 200
    assert len(sent) == 3


def test_new_link_retires_old_ones_after_a_reset(client, sent, monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://x.test")
    email, _ = signup(client)
    client.post("/auth/forgot", json={"email": email})
    first = token_from(sent)
    client.post("/auth/forgot", json={"email": email})
    second = token_from(sent)
    assert client.post("/auth/reset", json={"token": second, "password": NEW}).status_code == 200
    assert client.post("/auth/reset", json={"token": first, "password": "other-password-1"}).status_code == 400


def test_deactivated_and_suspended_people_get_no_email(client, sent, monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://x.test")
    email, admin = signup(client)
    tech_id, tech_email = add_tech(client, admin)
    client.patch(f"/team/{tech_id}", json={"active": False}, headers=admin)
    sent.clear()
    client.post("/auth/forgot", json={"email": tech_email})
    assert sent == []

    with Session(engine) as s:
        org = s.get(models.Organisation, s.exec(select(models.User).where(models.User.email == email)).one().org_id)
        org.suspended = True
        s.add(org)
        s.commit()
    client.post("/auth/forgot", json={"email": email})
    assert sent == []
