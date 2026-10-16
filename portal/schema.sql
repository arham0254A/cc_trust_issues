DROP TABLE IF EXISTS registrations;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'member' CHECK (role IN ('member', 'admin')),
    full_name     TEXT    NOT NULL DEFAULT '',
    email         TEXT    NOT NULL DEFAULT '',
    bio           TEXT    NOT NULL DEFAULT '',
    created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    starts_at   TEXT    NOT NULL,
    capacity    INTEGER NOT NULL CHECK (capacity > 0),
    created_by  INTEGER NOT NULL REFERENCES users (id)
);

CREATE TABLE registrations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    event_id   INTEGER NOT NULL REFERENCES events (id) ON DELETE CASCADE,
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, event_id)
);

CREATE TABLE login_attempts (
    bucket       TEXT    PRIMARY KEY,
    fails        INTEGER NOT NULL DEFAULT 0,
    locked_until REAL    NOT NULL DEFAULT 0
);
