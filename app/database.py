import json
import sqlite3
import hashlib
from pathlib import Path


DB_PATH = Path(__file__).parent / "data" / "assessment.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS exam_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                exam_mode TEXT DEFAULT 'practice',
                exam_key TEXT DEFAULT '',
                deadline TEXT DEFAULT '',
                exam_goal_json TEXT NOT NULL,
                score INTEGER NOT NULL,
                analysis_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );

            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                question_prompt TEXT NOT NULL,
                question_type TEXT NOT NULL,
                response TEXT NOT NULL,
                correct_answer TEXT,
                score REAL NOT NULL,
                is_correct INTEGER NOT NULL,
                ai_rationale TEXT,
                FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id)
            );
            """
        )
        existing_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(exam_attempts)")
        }
        if "exam_mode" not in existing_columns:
            connection.execute("ALTER TABLE exam_attempts ADD COLUMN exam_mode TEXT DEFAULT 'practice'")
        if "exam_key" not in existing_columns:
            connection.execute("ALTER TABLE exam_attempts ADD COLUMN exam_key TEXT DEFAULT ''")
        if "deadline" not in existing_columns:
            connection.execute("ALTER TABLE exam_attempts ADD COLUMN deadline TEXT DEFAULT ''")


def exam_key_from_goal(exam_goal):
    raw_key = "|".join(
        [
            exam_goal.get("target_role", ""),
            exam_goal.get("topic_focus", ""),
            exam_goal.get("difficulty", ""),
            exam_goal.get("exam_mode", "practice"),
        ]
    )
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]


def has_assessment_attempt(employee_id, exam_key):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id FROM exam_attempts
            WHERE employee_id = ?
              AND exam_key = ?
              AND exam_mode = 'assessment'
            LIMIT 1
            """,
            (employee_id, exam_key),
        ).fetchone()
        return row is not None


def save_exam_attempt(employee, exam_goal, score, answers, analysis):
    exam_mode = exam_goal.get("exam_mode", "practice")
    deadline = exam_goal.get("deadline", "")
    exam_key = exam_key_from_goal(exam_goal)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO employees (id, name, role)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                role = excluded.role
            """,
            (employee["id"], employee["name"], employee["role"]),
        )
        cursor = connection.execute(
            """
            INSERT INTO exam_attempts (
                employee_id,
                exam_mode,
                exam_key,
                deadline,
                exam_goal_json,
                score,
                analysis_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee["id"],
                exam_mode,
                exam_key,
                deadline,
                json.dumps(exam_goal),
                score,
                json.dumps(analysis),
            ),
        )
        attempt_id = cursor.lastrowid

        for answer in answers:
            connection.execute(
                """
                INSERT INTO answers (
                    attempt_id,
                    question_id,
                    question_prompt,
                    question_type,
                    response,
                    correct_answer,
                    score,
                    is_correct,
                    ai_rationale
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    answer["questionId"],
                    answer["prompt"],
                    answer["type"],
                    answer["response"],
                    answer.get("correctAnswer", ""),
                    answer["score"],
                    1 if answer["isCorrect"] else 0,
                    answer.get("aiRationale", ""),
                ),
            )

        return attempt_id
