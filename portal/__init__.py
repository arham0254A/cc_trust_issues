import os
import secrets
from datetime import timedelta

from flask import Flask, g, redirect, session, url_for

from . import db, security


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("PORTAL_SECRET_KEY") or secrets.token_hex(32),
        DATABASE=os.path.join(app.instance_path, "portal.sqlite"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("PORTAL_HTTPS") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
        MAX_CONTENT_LENGTH=64 * 1024,
        LOGIN_MAX_FAILS=5,
        LOGIN_IP_MAX_FAILS=20,
        LOGIN_LOCK_SECONDS=900,
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    @app.before_request
    def load_user():
        user_id = session.get("user_id")
        g.user = None
        if user_id is not None:
            g.user = db.get_db().execute(
                "SELECT id, username, role, full_name FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if g.user is None:
                session.clear()

    app.before_request(security.check_csrf)
    app.after_request(security.set_security_headers)
    app.jinja_env.globals["csrf_token"] = security.csrf_token

    from . import admin, auth, events, members
    app.register_blueprint(auth.bp)
    app.register_blueprint(members.bp)
    app.register_blueprint(events.bp)
    app.register_blueprint(admin.bp)

    @app.route("/")
    def index():
        return redirect(url_for("events.list_events"))

    return app
