
import sqlite3
import json
from pathlib import Path


DB_PATH = Path("data/candidates.db")


def get_connection():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return sqlite3.connect(DB_PATH)


def initialize_database():

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                job_title TEXT,
                resume_text TEXT,
                screening_report TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_candidate(
    name,
    email,
    phone,
    job_title,
    resume_text,
    report
):

    with get_connection() as connection:

        cursor = connection.execute("""
            INSERT INTO candidates (
                name,
                email,
                phone,
                job_title,
                resume_text,
                screening_report
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            job_title,
            resume_text,
            json.dumps(report)
        ))

        return cursor.lastrowid


def get_candidates():

    with get_connection() as connection:

        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT
                id,
                name,
                email,
                phone,
                job_title,
                screening_report,
                created_at
            FROM candidates
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def delete_candidate(candidate_id):

    with get_connection() as connection:

        connection.execute(
            "DELETE FROM candidates WHERE id = ?",
            (candidate_id,)
        )
