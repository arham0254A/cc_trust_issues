from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .db import get_db
from .security import login_required

bp = Blueprint("members", __name__, url_prefix="/me")

EDITABLE_FIELDS = {"full_name": 100, "email": 254, "bio": 1000}


@bp.route("/", methods=("GET", "POST"))
@login_required
def profile():
    db = get_db()
    if request.method == "POST":
        values = {f: request.form.get(f, "").strip() for f in EDITABLE_FIELDS}
        errors = [f for f, limit in EDITABLE_FIELDS.items() if len(values[f]) > limit]
        if values["email"] and "@" not in values["email"]:
            errors.append("email")
        if errors:
            flash("Please check: " + ", ".join(errors))
        else:
            db.execute(
                "UPDATE users SET full_name = ?, email = ?, bio = ? WHERE id = ?",
                (values["full_name"], values["email"], values["bio"], g.user["id"]),
            )
            db.commit()
            flash("Profile updated.")
            return redirect(url_for("members.profile"))

    user = db.execute(
        "SELECT username, role, full_name, email, bio FROM users WHERE id = ?", (g.user["id"],)
    ).fetchone()
    my_events = db.execute(
        "SELECT e.id, e.title, e.starts_at FROM events e"
        " JOIN registrations r ON r.event_id = e.id"
        " WHERE r.user_id = ? ORDER BY e.starts_at",
        (g.user["id"],),
    ).fetchall()
    return render_template("members/profile.html", user=user, my_events=my_events)
