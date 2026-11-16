import sqlite3
import json
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = os.environ.get("SQLITE_DB_PATH", str(BASE_DIR / "pathpilot.db"))


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def init_db(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS demo_sessions (
        id TEXT PRIMARY KEY,
        token_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS profiles (
        session_id TEXT PRIMARY KEY REFERENCES demo_sessions(id) ON DELETE CASCADE,
        daily_minutes INTEGER NOT NULL DEFAULT 45,
        language TEXT NOT NULL DEFAULT 'en'
    );

    CREATE TABLE IF NOT EXISTS skills (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        skill_order INTEGER NOT NULL,
        prerequisites_json TEXT NOT NULL,
        estimated_recovery_mins INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS questions (
        id TEXT PRIMARY KEY,
        version INTEGER NOT NULL,
        skill_id TEXT NOT NULL REFERENCES skills(id),
        purpose TEXT NOT NULL,
        stem TEXT NOT NULL,
        options_json TEXT NOT NULL,
        answer_key TEXT NOT NULL,
        distractor_tags_json TEXT NOT NULL,
        explanation TEXT NOT NULL,
        reviewed_by TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS assessments (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES demo_sessions(id) ON DELETE CASCADE,
        kind TEXT NOT NULL,
        skill_id TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        completed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS assessment_items (
        id TEXT PRIMARY KEY,
        assessment_id TEXT NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
        question_id TEXT NOT NULL REFERENCES questions(id),
        ordinal INTEGER NOT NULL,
        UNIQUE(assessment_id, question_id)
    );

    CREATE TABLE IF NOT EXISTS answers (
        id TEXT PRIMARY KEY,
        assessment_item_id TEXT NOT NULL UNIQUE REFERENCES assessment_items(id) ON DELETE CASCADE,
        selected_option TEXT NOT NULL,
        correctness INTEGER NOT NULL,
        distractor_tag TEXT,
        skipped INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS plans (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES demo_sessions(id) ON DELETE CASCADE,
        version INTEGER NOT NULL,
        available_minutes INTEGER NOT NULL,
        scheduled_minutes INTEGER NOT NULL,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(session_id, version)
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        plan_id TEXT NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
        skill_id TEXT NOT NULL REFERENCES skills(id),
        kind TEXT NOT NULL,
        minutes INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        source_task_id TEXT,
        title TEXT NOT NULL,
        description TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS agent_runs (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES demo_sessions(id) ON DELETE CASCADE,
        status TEXT NOT NULL,
        requested_action TEXT NOT NULL,
        user_message TEXT NOT NULL,
        tool_result_json TEXT,
        reply_text TEXT NOT NULL,
        llm_mode TEXT NOT NULL,
        error_code TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS idempotency_keys (
        session_id TEXT NOT NULL REFERENCES demo_sessions(id) ON DELETE CASCADE,
        route TEXT NOT NULL,
        key TEXT NOT NULL,
        request_hash TEXT NOT NULL,
        response_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (session_id, route, key)
    );

    CREATE TABLE IF NOT EXISTS cutoffs (
        id TEXT PRIMARY KEY,
        cohort_key TEXT NOT NULL,
        institution TEXT NOT NULL,
        program TEXT NOT NULL,
        year INTEGER NOT NULL,
        round INTEGER NOT NULL,
        quota TEXT NOT NULL,
        seat_category TEXT NOT NULL,
        gender_pool TEXT NOT NULL,
        rank_type TEXT NOT NULL,
        opening_rank INTEGER NOT NULL,
        closing_rank INTEGER NOT NULL,
        source_url TEXT NOT NULL,
        retrieved_at TEXT NOT NULL
    );
    """)
    if "deferred_tasks_json" not in {row["name"] for row in conn.execute("PRAGMA table_info(plans)")}:
        conn.execute("ALTER TABLE plans ADD COLUMN deferred_tasks_json TEXT NOT NULL DEFAULT '[]'")
    conn.commit()

    # Seed data
    seed_data(conn)
    conn.close()


def seed_data(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # 1. Skills
    skills_path = DATA_DIR / "skills.json"
    if skills_path.exists():
        with open(skills_path, "r", encoding="utf-8") as f:
            skills = json.load(f)
            for s in skills:
                cursor.execute("""
                INSERT OR REPLACE INTO skills (id, title, description, skill_order, prerequisites_json, estimated_recovery_mins)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    s["id"],
                    s["title"],
                    s["description"],
                    s["order"],
                    json.dumps(s.get("prerequisites", [])),
                    s.get("estimated_recovery_mins", 25)
                ))

    # 2. Questions
    questions_path = DATA_DIR / "questions.json"
    if questions_path.exists():
        with open(questions_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
            for q in questions:
                cursor.execute("""
                INSERT OR IGNORE INTO questions (
                    id, version, skill_id, purpose, stem, options_json, answer_key, distractor_tags_json, explanation, reviewed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    q["id"],
                    q["version"],
                    q["skill_id"],
                    q["purpose"],
                    q["stem"],
                    json.dumps(q["options"]),
                    q["answer_key"],
                    json.dumps(q.get("distractor_tags", {})),
                    q["explanation"],
                    q["reviewed_by"]
                ))

    # 3. Cutoffs
    cutoffs_path = DATA_DIR / "cutoffs.json"
    if cutoffs_path.exists():
        with open(cutoffs_path, "r", encoding="utf-8") as f:
            cutoff_data = json.load(f)
            # Replace the bundled dataset, including rows retired by the next release.
            cursor.execute("DELETE FROM cutoffs")
            for row in cutoff_data.get("cutoff_rows", []):
                cursor.execute("""
                INSERT OR REPLACE INTO cutoffs (
                    id, cohort_key, institution, program, year, round, quota, seat_category, gender_pool, rank_type, opening_rank, closing_rank, source_url, retrieved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["id"],
                    row["cohort_key"],
                    row["institution"],
                    row["program"],
                    row["year"],
                    row["round"],
                    row["quota"],
                    row["seat_category"],
                    row["gender_pool"],
                    row["rank_type"],
                    row["opening_rank"],
                    row["closing_rank"],
                    row["source_url"],
                    row["retrieved_at"]
                ))

    conn.commit()


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

