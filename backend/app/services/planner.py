import sqlite3
import uuid
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from ..schemas import PlanOut, TaskOut, DeferredTaskOut, PlanDiffOut, ReplanResponse
from .grading import get_skill_evidence


class ConcurrencyConflictError(Exception):
    def __init__(self, current_version: int, expected_version: int):
        self.current_version = current_version
        self.expected_version = expected_version
        super().__init__(f"Plan version mismatch: expected {expected_version}, but current is {current_version}")


def get_current_plan(conn: sqlite3.Connection, session_id: str) -> Optional[PlanOut]:
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, session_id, version, available_minutes, scheduled_minutes, reason, created_at, deferred_tasks_json
    FROM plans
    WHERE session_id = ?
    ORDER BY version DESC
    LIMIT 1
    """, (session_id,))
    plan_row = cursor.fetchone()
    if not plan_row:
        return None

    plan_id = plan_row["id"]
    cursor.execute("""
    SELECT id, plan_id, skill_id, kind, minutes, status, source_task_id, title, description
    FROM tasks
    WHERE plan_id = ?
    ORDER BY rowid ASC
    """, (plan_id,))
    task_rows = cursor.fetchall()

    tasks = [
        TaskOut(
            id=t["id"],
            plan_id=t["plan_id"],
            skill_id=t["skill_id"],
            kind=t["kind"],
            minutes=t["minutes"],
            status=t["status"],
            source_task_id=t["source_task_id"],
            title=t["title"],
            description=t["description"]
        ) for t in task_rows
    ]

    return PlanOut(
        id=plan_row["id"],
        session_id=plan_row["session_id"],
        version=plan_row["version"],
        available_minutes=plan_row["available_minutes"],
        scheduled_minutes=plan_row["scheduled_minutes"],
        reason=plan_row["reason"],
        created_at=plan_row["created_at"],
        tasks=tasks,
        deferred_tasks=json.loads(plan_row["deferred_tasks_json"])
    )


def generate_plan(
    conn: sqlite3.Connection,
    session_id: str,
    available_minutes: int,
    reason: str = "Plan generation",
    expected_version: Optional[int] = None
) -> Tuple[PlanOut, List[DeferredTaskOut], PlanDiffOut]:
    cursor = conn.cursor()
    previous_plan = get_current_plan(conn, session_id)

    # Check optimistic concurrency if expected_version is provided
    cursor.execute("""
    SELECT version FROM plans WHERE session_id = ? ORDER BY version DESC LIMIT 1
    """, (session_id,))
    latest_row = cursor.fetchone()
    latest_version = latest_row["version"] if latest_row else 0

    if expected_version is not None and latest_version != expected_version:
        raise ConcurrencyConflictError(latest_version, expected_version)

    # Fetch previously completed tasks across all plan versions for this session
    cursor.execute("""
    SELECT t.skill_id, t.kind, t.status
    FROM tasks t
    JOIN plans p ON t.plan_id = p.id
    WHERE p.session_id = ? AND t.status = 'completed'
    """, (session_id,))
    completed_task_keys = {(r["skill_id"], r["kind"]) for r in cursor.fetchall()}

    # 1. Gather skill evidence
    evidences = get_skill_evidence(conn, session_id)
    # Sort skills by weakness: lower correct ratio first, tie-break by vector_components -> vector_addition -> constant_accel_1d
    def sort_key(e):
        ratio = (
            e.practice_correct / e.practice_attempted if e.practice_attempted == e.practice_total and e.practice_total
            else e.diagnostic_correct / e.diagnostic_attempted if e.diagnostic_attempted
            else 2
        )
        order_bias = 0
        if e.skill_id == "vector_components":
            order_bias = 1
        elif e.skill_id == "vector_addition":
            order_bias = 2
        else:
            order_bias = 3
        return (ratio, order_bias)

    sorted_skills = sorted(evidences, key=sort_key)
    assessed = [skill for skill in sorted_skills if skill.diagnostic_attempted or skill.practice_attempted]
    if assessed:
        sorted_skills = assessed
    if len(sorted_skills) > 1 and sorted_skills[0].skill_id == "vector_addition":
        prerequisite = next((s for s in sorted_skills if s.skill_id == "vector_components"), None)
        if prerequisite and sort_key(prerequisite)[0] < 1:
            sorted_skills.remove(prerequisite)
            sorted_skills.insert(0, prerequisite)

    # Candidate task builder
    candidate_tasks = []
    # Primary weak skill
    weakest = sorted_skills[0] if sorted_skills else None
    second_weakest = sorted_skills[1] if len(sorted_skills) > 1 else None
    third_skill = sorted_skills[2] if len(sorted_skills) > 2 else None

    if weakest:
        candidate_tasks.append({
            "skill_id": weakest.skill_id,
            "kind": "learn",
            "minutes": 10,
            "title": f"Concept Review: {weakest.title}",
            "description": "Review the key formulas and common pitfalls in this skill's mentor notes."
        })
        candidate_tasks.append({
            "skill_id": weakest.skill_id,
            "kind": "practice",
            "minutes": 15,
            "title": f"Fresh Practice: {weakest.title}",
            "description": "Work through the practice questions for this skill."
        })

    if second_weakest:
        candidate_tasks.append({
            "skill_id": second_weakest.skill_id,
            "kind": "review",
            "minutes": 5,
            "title": f"Rapid Recall: {second_weakest.title}",
            "description": "5-minute formula reinforcement and quick checkpoint."
        })
        candidate_tasks.append({
            "skill_id": second_weakest.skill_id,
            "kind": "learn",
            "minutes": 10,
            "title": f"Concept Study: {second_weakest.title}",
            "description": "Study the worked examples and review the key formulas."
        })
        candidate_tasks.append({
            "skill_id": second_weakest.skill_id,
            "kind": "practice",
            "minutes": 15,
            "title": f"Fresh Practice: {second_weakest.title}",
            "description": "Work through the practice questions for this skill."
        })

    if third_skill:
        candidate_tasks.append({
            "skill_id": third_skill.skill_id,
            "kind": "review",
            "minutes": 10,
            "title": f"Skill Review: {third_skill.title}",
            "description": "Recall the key formulas and check when they apply."
        })

    # Fit within available minutes
    scheduled_tasks: List[Dict[str, Any]] = []
    deferred_tasks: List[DeferredTaskOut] = []
    remaining_mins = available_minutes

    for task in candidate_tasks:
        if task["kind"] == "practice" and any(
            e.skill_id == task["skill_id"] and e.practice_attempted >= e.practice_total
            for e in evidences
        ):
            continue
        if task["minutes"] <= remaining_mins:
            scheduled_tasks.append(task)
            remaining_mins -= task["minutes"]
        else:
            deferred_tasks.append(DeferredTaskOut(
                skill_id=task["skill_id"],
                kind=task["kind"],
                minutes=task["minutes"],
                title=task["title"],
                reason=f"Deferred due to daily time constraint of {available_minutes} minutes"
            ))

    total_scheduled = sum(t["minutes"] for t in scheduled_tasks)

    # Atomically write new plan
    new_version = latest_version + 1
    new_plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
    INSERT INTO plans (id, session_id, version, available_minutes, scheduled_minutes, reason, created_at, deferred_tasks_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_plan_id,
        session_id,
        new_version,
        available_minutes,
        total_scheduled,
        reason,
        now_iso,
        json.dumps([item.model_dump() for item in deferred_tasks])
    ))

    task_objects: List[TaskOut] = []
    for t in scheduled_tasks:
        t_id = f"task_{uuid.uuid4().hex[:12]}"
        # If task was previously completed, preserve status!
        is_previously_completed = (t["skill_id"], t["kind"]) in completed_task_keys
        status = "completed" if is_previously_completed else "pending"

        cursor.execute("""
        INSERT INTO tasks (id, plan_id, skill_id, kind, minutes, status, title, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t_id,
            new_plan_id,
            t["skill_id"],
            t["kind"],
            t["minutes"],
            status,
            t["title"],
            t["description"]
        ))

        task_objects.append(TaskOut(
            id=t_id,
            plan_id=new_plan_id,
            skill_id=t["skill_id"],
            kind=t["kind"],
            minutes=t["minutes"],
            status=status,
            title=t["title"],
            description=t["description"]
        ))

    # Diff calculation
    prev_titles = [pt.title for pt in previous_plan.tasks] if previous_plan else []
    new_titles = [nt.title for nt in task_objects]

    added = [t for t in new_titles if t not in prev_titles]
    removed = [t for t in prev_titles if t not in new_titles]
    retained = [t for t in new_titles if t in prev_titles]
    minutes_diff = total_scheduled - (previous_plan.scheduled_minutes if previous_plan else 0)

    diff = PlanDiffOut(
        previous_version=latest_version,
        new_version=new_version,
        added_tasks=added,
        removed_tasks=removed,
        retained_tasks=retained,
        minutes_diff=minutes_diff
    )

    created_plan = PlanOut(
        id=new_plan_id,
        session_id=session_id,
        version=new_version,
        available_minutes=available_minutes,
        scheduled_minutes=total_scheduled,
        reason=reason,
        created_at=now_iso,
        tasks=task_objects,
        deferred_tasks=deferred_tasks
    )

    return created_plan, deferred_tasks, diff


def update_task_status(conn: sqlite3.Connection, session_id: str, task_id: str, new_status: str) -> TaskOut:
    cursor = conn.cursor()
    # Verify ownership through plan
    cursor.execute("""
    SELECT t.id, t.plan_id, t.skill_id, t.kind, t.minutes, t.status, t.source_task_id, t.title, t.description
    FROM tasks t
    JOIN plans p ON t.plan_id = p.id
    WHERE t.id = ? AND p.session_id = ?
      AND p.version = (SELECT MAX(version) FROM plans WHERE session_id = p.session_id)
    """, (task_id, session_id))
    row = cursor.fetchone()
    if not row:
        raise ValueError("Task not found or access denied")

    cursor.execute("""
    UPDATE tasks
    SET status = ?
    WHERE id = ?
    """, (new_status, task_id))

    return TaskOut(
        id=row["id"],
        plan_id=row["plan_id"],
        skill_id=row["skill_id"],
        kind=row["kind"],
        minutes=row["minutes"],
        status=new_status,
        source_task_id=row["source_task_id"],
        title=row["title"],
        description=row["description"]
    )

