"""
All the database work lives here (Lesson 12).

Keeping the database code in its own file makes app.py shorter and easier to
read. app.py just imports these functions and uses them.
"""

import sqlite3

# Our database file. It stores every review we ever analyze.
DB_FILE = "feedback.db"


def init_db():
    """Create the feedback table and add session isolation if needed."""
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY,
                review TEXT,
                label TEXT,
                score INTEGER,
                theme TEXT,
                session_id TEXT
            )
        """)

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(feedback)").fetchall()
        }
        if "session_id" not in columns:
            conn.execute("ALTER TABLE feedback ADD COLUMN session_id TEXT")

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_feedback_session_id "
            "ON feedback(session_id, id)"
        )
        conn.commit()
    finally:
        conn.close()


def save_results(results, session_id):
    """Write analyzed reviews scoped to the current app session."""
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.executemany(
            """
            INSERT INTO feedback (review, label, score, theme, session_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (r["review"], r["label"], r["score"], r["theme"], session_id)
                for r in results
            ],
        )
        conn.commit()
    finally:
        conn.close()


def load_history(session_id):
    """Read only reviews saved by the current app session."""
    conn = sqlite3.connect(DB_FILE)
    try:
        return conn.execute(
            """
            SELECT review, label, score, theme
            FROM feedback
            WHERE session_id = ?
            ORDER BY id DESC
            """,
            (session_id,),
        ).fetchall()
    finally:
        conn.close()
