import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from ..schemas import SkillEvidence, AnswerResult


def ensure_assessment(conn: sqlite3.Connection, session_id: str, kind: str, skill_id: str | None) -> str:
    """Resume the same assessment instead of accumulating evidence from repeat items."""
    existing = conn.execute("""
        SELECT s.id FROM assessments s
        WHERE s.session_id = ? AND s.kind = ? AND s.skill_id IS ?
        ORDER BY (SELECT COUNT(*) FROM assessment_items i JOIN answers a ON a.assessment_item_id = i.id
                  WHERE i.assessment_id = s.id) DESC, s.created_at ASC LIMIT 1
    """, (session_id, kind, skill_id)).fetchone()
    if existing:
        return existing["id"]

    questions = conn.execute("""
        SELECT q.id FROM questions q JOIN skills s ON q.skill_id = s.id
        WHERE q.purpose = ? AND (? IS NULL OR q.skill_id = ?)
        ORDER BY s.skill_order, q.id LIMIT ?
    """, (kind, skill_id, skill_id, 9 if kind == "diagnostic" else 3)).fetchall()
    if not questions:
        raise ValueError("No questions available for this skill")

    assessment_id = f"ass_{uuid.uuid4().hex}"
    conn.execute("""
        INSERT INTO assessments (id, session_id, kind, skill_id, status, created_at)
        VALUES (?, ?, ?, ?, 'in_progress', ?)
    """, (assessment_id, session_id, kind, skill_id, datetime.now(timezone.utc).isoformat()))
    conn.executemany("""
        INSERT INTO assessment_items (id, assessment_id, question_id, ordinal) VALUES (?, ?, ?, ?)
    """, [
        (f"item_{uuid.uuid4().hex}", assessment_id, q["id"], index)
        for index, q in enumerate(questions)
    ])
    return assessment_id


def submit_answer(
    conn: sqlite3.Connection,
    assessment_item_id: str,
    selected_option: str,
    skipped: bool = False
) -> AnswerResult:
    cursor = conn.cursor()

    # Verify assessment item and question
    cursor.execute("""
    SELECT ai.id, ai.assessment_id, ai.question_id, ai.ordinal,
           q.answer_key, q.distractor_tags_json, q.explanation
    FROM assessment_items ai
    JOIN questions q ON ai.question_id = q.id
    WHERE ai.id = ?
    """, (assessment_item_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError("Assessment item not found")

    assessment_id = row["assessment_id"]
    answer_key = row["answer_key"]
    distractor_tags = json.loads(row["distractor_tags_json"]) if row["distractor_tags_json"] else {}
    explanation = row["explanation"]

    # Check if already answered
    cursor.execute("SELECT id FROM answers WHERE assessment_item_id = ?", (assessment_item_id,))
    existing = cursor.fetchone()
    if existing:
        raise ValueError("Answer already submitted for this item")

    is_correct = (selected_option.strip().upper() == answer_key.strip().upper()) and not skipped
    distractor_tag = None
    if not is_correct and not skipped:
        distractor_tag = distractor_tags.get(selected_option.strip().upper())

    answer_id = f"ans_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
    INSERT INTO answers (id, assessment_item_id, selected_option, correctness, distractor_tag, skipped, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        answer_id,
        assessment_item_id,
        selected_option.strip().upper(),
        1 if is_correct else 0,
        distractor_tag,
        1 if skipped else 0,
        now_iso
    ))

    # Check next item in assessment
    cursor.execute("""
    SELECT ai.id
    FROM assessment_items ai
    LEFT JOIN answers a ON a.assessment_item_id = ai.id
    WHERE ai.assessment_id = ? AND a.id IS NULL
    ORDER BY ai.ordinal ASC
    LIMIT 1
    """, (assessment_id,))
    next_item = cursor.fetchone()
    next_question_id = next_item["id"] if next_item else None

    # Check if assessment is complete
    cursor.execute("""
    SELECT COUNT(ai.id) as total_items, COUNT(a.id) as answered_items
    FROM assessment_items ai
    LEFT JOIN answers a ON a.assessment_item_id = ai.id
    WHERE ai.assessment_id = ?
    """, (assessment_id,))
    counts = cursor.fetchone()
    is_completed = (counts["total_items"] == counts["answered_items"])
    if is_completed:
        cursor.execute("""
        UPDATE assessments
        SET status = 'completed', completed_at = ?
        WHERE id = ?
        """, (now_iso, assessment_id))

    return AnswerResult(
        answer_id=answer_id,
        question_id=assessment_item_id,
        selected_option=selected_option.strip().upper(),
        correctness=is_correct,
        correct_option=answer_key,
        distractor_tag=distractor_tag,
        explanation=explanation,
        is_completed=is_completed,
        next_question_id=next_question_id
    )


def get_skill_evidence(conn: sqlite3.Connection, session_id: str) -> List[SkillEvidence]:
    cursor = conn.cursor()

    # Fetch all skills
    cursor.execute("SELECT id, title, skill_order FROM skills ORDER BY skill_order ASC")
    skills = cursor.fetchall()

    evidence_list: List[SkillEvidence] = []

    for s in skills:
        skill_id = s["id"]
        title = s["title"]

        # Diagnostic answers
        cursor.execute("""
        SELECT a.correctness, a.distractor_tag, q.id AS question_id
        FROM answers a
        JOIN assessment_items ai ON a.assessment_item_id = ai.id
        JOIN assessments ass ON ai.assessment_id = ass.id
        JOIN questions q ON ai.question_id = q.id
        WHERE ass.session_id = ? AND q.skill_id = ? AND ass.kind = 'diagnostic' AND a.skipped = 0
        ORDER BY a.created_at
        """, (session_id, skill_id))
        diag_rows = first_attempts(cursor.fetchall())

        diag_total = 3  # exactly 3 diagnostic questions in this pack
        diag_attempted = len(diag_rows)
        diag_correct = sum(1 for r in diag_rows if r["correctness"] == 1)

        misconceptions = [r["distractor_tag"] for r in diag_rows if r["distractor_tag"]]

        # Practice answers
        cursor.execute("""
        SELECT a.correctness, a.distractor_tag, q.id AS question_id
        FROM answers a
        JOIN assessment_items ai ON a.assessment_item_id = ai.id
        JOIN assessments ass ON ai.assessment_id = ass.id
        JOIN questions q ON ai.question_id = q.id
        WHERE ass.session_id = ? AND q.skill_id = ? AND ass.kind = 'practice' AND a.skipped = 0
        ORDER BY a.created_at
        """, (session_id, skill_id))
        prac_rows = first_attempts(cursor.fetchall())

        prac_total = 3  # exactly 3 fresh practice questions in this pack
        prac_attempted = len(prac_rows)
        prac_correct = sum(1 for r in prac_rows if r["correctness"] == 1)

        # Status logic
        if diag_attempted == 0:
            status = "not_assessed"
        elif diag_correct == diag_total:
            status = "proficient"
        else:
            status = "needs_practice"

        caveat = "Small sample (3 questions). Demonstrates immediate diagnostic pattern, not durable exam mastery."

        evidence_list.append(SkillEvidence(
            skill_id=skill_id,
            title=title,
            diagnostic_correct=diag_correct,
            diagnostic_attempted=diag_attempted,
            diagnostic_total=diag_total,
            practice_correct=prac_correct,
            practice_attempted=prac_attempted,
            practice_total=prac_total,
            status=status,
            evidence_caveat=caveat,
            misconceptions=list(dict.fromkeys(misconceptions))  # unique tags
        ))

    return evidence_list


def first_attempts(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    by_question: dict[str, sqlite3.Row] = {}
    for row in rows:
        by_question.setdefault(row["question_id"], row)
    return list(by_question.values())

