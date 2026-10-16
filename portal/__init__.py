import os

from flask import Flask, g, redirect, session, url_for

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # WEAKNESS
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "portal_vuln.sqlite"),
        # WEAKNESS
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_SAMESITE=None,
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    # WEAKNESS
    app.jinja_env.globals["csrf_token"] = lambda: ""

    @app.before_request
    def load_user():
        user_id = session.get("user_id")
        g.user = None
        if user_id is not None:
            g.user = db.get_db().execute(
                "SELECT id, username, role, full_name FROM users WHERE id = ?", (user_id,)
            ).fetchone()

    from . import admin, auth, events, members
    app.register_blueprint(auth.bp)
    app.register_blueprint(members.bp)
    app.register_blueprint(events.bp)
    app.register_blueprint(admin.bp)

    @app.route("/")
    def index():
        return redirect(url_for("events.list_events"))

    return app
