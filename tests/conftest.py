import re

import pytest
from werkzeug.security import generate_password_hash

from portal import create_app
from portal.db import get_db, init_db


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.sqlite"),
        "SECRET_KEY": "test",
        "LOGIN_MAX_FAILS": 3,
        "LOGIN_IP_MAX_FAILS": 50,
        "LOGIN_LOCK_SECONDS": 300,
    })
    with app.app_context():
        init_db()
        db = get_db()
        for name, role in (("riya", "member"), ("aditya", "member"), ("admin", "admin")):
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (name, generate_password_hash("correct-horse"), role),
            )
        db.execute(
            "INSERT INTO events (title, starts_at, capacity, created_by) VALUES ('Hackathon', '2026-11-01T10:00', 1, 3)"
        )
        db.commit()
    return app


class Client:
    """Test client that fetches and sends the CSRF token like a browser would."""

    def __init__(self, app):
        self.c = app.test_client()

    def token(self):
        html = self.c.get("/auth/login").get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

    def get(self, url):
        return self.c.get(url)

    def post(self, url, data=None, token=True):
        data = dict(data or {})
        if token:
            data["csrf_token"] = self.token()
        return self.c.post(url, data=data)

    def login(self, username, password="correct-horse"):
        return self.post("/auth/login", {"username": username, "password": password})


@pytest.fixture
def client(app):
    return Client(app)
