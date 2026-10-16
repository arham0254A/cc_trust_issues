from flask import Blueprint, abort, flash, g, redirect, render_template, url_for

from .db import get_db
from .members import login_required

bp = Blueprint("events", __name__, url_prefix="/events")


def _get_event(event_id):
    event = get_db().execute(
        "SELECT e.*, (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id) AS taken"
        " FROM events e WHERE e.id = ?",
        (event_id,),
    ).fetchone()
    if event is None:
        abort(404)
    return event


@bp.route("/")
@login_required
def list_events():
    events = get_db().execute(
        "SELECT e.id, e.title, e.starts_at, e.capacity,"
        " (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.id) AS taken,"
        " EXISTS(SELECT 1 FROM registrations r WHERE r.event_id = e.id AND r.user_id = ?) AS mine"
        " FROM events e ORDER BY e.starts_at",
        (g.user["id"],),
    ).fetchall()
    return render_template("events/list.html", events=events)


@bp.route("/<int:event_id>")
@login_required
def detail(event_id):
    event = _get_event(event_id)
    mine = get_db().execute(
        "SELECT 1 FROM registrations WHERE event_id = ? AND user_id = ?",
        (event_id, g.user["id"]),
    ).fetchone()
    return render_template("events/detail.html", event=event, mine=mine is not None)


@bp.route("/<int:event_id>/register", methods=("POST",))
@login_required
def register(event_id):
    db = get_db()
    cur = db.execute(
        "INSERT OR IGNORE INTO registrations (user_id, event_id)"
        " SELECT ?, id FROM events WHERE id = ?"
        " AND capacity > (SELECT COUNT(*) FROM registrations WHERE event_id = ?)",
        (g.user["id"], event_id, event_id),
    )
    db.commit()
    flash("You're registered." if cur.rowcount else "Could not register (full, missing, or already registered).")
    return redirect(url_for("events.detail", event_id=event_id))


@bp.route("/<int:event_id>/unregister", methods=("POST",))
@login_required
def unregister(event_id):
    db = get_db()
    db.execute(
        "DELETE FROM registrations WHERE event_id = ? AND user_id = ?", (event_id, g.user["id"])
    )
    db.commit()
    flash("Registration cancelled.")
    return redirect(url_for("events.detail", event_id=event_id))
