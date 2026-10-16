import time

from flask import current_app

from .db import get_db


def _now():
    return time.time()


def is_locked(bucket):
    """True if this bucket is currently in a lock window."""
    row = get_db().execute(
        "SELECT locked_until FROM login_attempts WHERE bucket = ?", (bucket,)
    ).fetchone()
    return bool(row) and row["locked_until"] > _now()


def any_locked(*buckets):
    return any(is_locked(b) for b in buckets)


def record_failure(bucket, max_fails, lock_seconds):
    """Count a failed attempt for this bucket and lock it once it hits max_fails."""
    db = get_db()
    db.execute(
        "INSERT INTO login_attempts (bucket, fails) VALUES (?, 1)"
        " ON CONFLICT(bucket) DO UPDATE SET fails = fails + 1",
        (bucket,),
    )
    row = db.execute("SELECT fails FROM login_attempts WHERE bucket = ?", (bucket,)).fetchone()
    if row and row["fails"] >= max_fails:
        db.execute(
            "UPDATE login_attempts SET locked_until = ? WHERE bucket = ?",
            (_now() + lock_seconds, bucket),
        )
    db.commit()


def reset(bucket):
    """Clear a bucket after a successful login."""
    db = get_db()
    db.execute("DELETE FROM login_attempts WHERE bucket = ?", (bucket,))
    db.commit()


def login_buckets(username, remote_addr):
    return f"user:{(username or '').strip().lower()}", f"ip:{remote_addr or 'unknown'}"
