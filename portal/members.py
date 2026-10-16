import functools

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .db import get_db

bp = Blueprint("members", __name__, url_prefix="/me")


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped


@bp.route("/")
@login_required
def profile():
    return redirect(url_for("members.view_user", user_id=g.user["id"]))


# VULN #3
@bp.route("/user/<int:user_id>", methods=("GET", "POST"))
@login_required
def view_user(user_id):
    db = get_db()
    if request.method == "POST":
        db.execute(
            "UPDATE users SET full_name = ?, email = ?, bio = ? WHERE id = ?",
            (
                request.form.get("full_name", ""),
                request.form.get("email", ""),
                request.form.get("bio", ""),
                user_id,
            ),
        )
        db.commit()
        flash("Profile updated.")
        return redirect(url_for("members.view_user", user_id=user_id))

    user = db.execute(
        "SELECT username, role, full_name, email, bio FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    my_events = db.execute(
        "SELECT e.id, e.title, e.starts_at FROM events e"
        " JOIN registrations r ON r.event_id = e.id WHERE r.user_id = ?",
        (user_id,),
    ).fetchall()
    return render_template("members/profile.html", user=user, my_events=my_events)
