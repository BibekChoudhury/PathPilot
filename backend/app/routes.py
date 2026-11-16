import os
import secrets
import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
import sqlite3

from .db import get_db, hash_token
from .schemas import (
    DemoSessionOut, ProfileOut, ProfileUpdate, AssessmentCreate, AssessmentOut,
    QuestionPublic, QuestionOption, AnswerSubmit, AnswerResult, AssessmentResultOut,
    ProgressOut, PlanCreate, PlanOut, ReplanRequest, ReplanResponse, TaskStatusUpdate,
    TaskOut, MentorRunRequest, AgentRunOut, ScenarioRequest, ScenarioResultOut
)
from .services.grading import ensure_assessment, submit_answer, get_skill_evidence
from .services.planner import generate_plan, get_current_plan, update_task_status, ConcurrencyConflictError
from .services.scenarios import compare_historical_rank
from .services.mentor import mentor_service

router = APIRouter(prefix="/api/v1")


# --- Authentication Dependency ---
def get_current_session(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_session_token: Optional[str] = Header(None),
    conn: sqlite3.Connection = Depends(get_db)
) -> Dict[str, Any]:
    token = None
    # 1. X-Session-Token header (takes explicit precedence)
    if x_session_token:
        token = x_session_token
    # 2. Authorization Bearer header
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    # 3. Cookie fallback
    elif "pathpilot_session" in request.cookies:
        token = request.cookies.get("pathpilot_session")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Missing session token", "retryable": False}
        )

    t_hash = hash_token(token)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT s.id, s.token_hash, s.created_at, s.expires_at, p.daily_minutes, p.language
    FROM demo_sessions s
    LEFT JOIN profiles p ON s.id = p.session_id
    WHERE s.token_hash = ?
    """, (t_hash,))
    row = cursor.fetchone()

    if not row or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or expired session token", "retryable": False}
        )

    return {
        "session_id": row["id"],
        "token": token,
        "daily_minutes": row["daily_minutes"] or 45,
        "language": row["language"] or "en"
    }


# --- Idempotency Helper ---
def check_idempotency(
    conn: sqlite3.Connection,
    session_id: str,
    route: str,
    idempotency_key: Optional[str],
    request_data: Any
) -> Optional[Dict[str, Any]]:
    if not idempotency_key:
        return None

    req_json = json.dumps(request_data, sort_keys=True)
    req_hash = hashlib.sha256(req_json.encode("utf-8")).hexdigest()

    cursor = conn.cursor()
    cursor.execute("""
    SELECT request_hash, response_json FROM idempotency_keys
    WHERE session_id = ? AND route = ? AND key = ?
    """, (session_id, route, idempotency_key))
    existing = cursor.fetchone()

    if existing:
        if existing["request_hash"] != req_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "IDEMPOTENCY_CONFLICT", "message": "Idempotency key reused with different payload", "retryable": False}
            )
        return json.loads(existing["response_json"])

    return None


def record_idempotency(
    conn: sqlite3.Connection,
    session_id: str,
    route: str,
    idempotency_key: Optional[str],
    request_data: Any,
    response_data: Any
):
    if not idempotency_key:
        return

    req_json = json.dumps(request_data, sort_keys=True)
    req_hash = hashlib.sha256(req_json.encode("utf-8")).hexdigest()
    res_json = json.dumps(response_data)
    now_iso = datetime.now(timezone.utc).isoformat()

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO idempotency_keys (session_id, route, key, request_hash, response_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, route, idempotency_key, req_hash, res_json, now_iso))


# --- 1. Session Endpoints ---
@router.post("/demo-sessions", response_model=DemoSessionOut)
def create_demo_session(request: Request, response: Response, conn: sqlite3.Connection = Depends(get_db)):
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    raw_token = secrets.token_urlsafe(32)
    t_hash = hash_token(raw_token)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=7)

    now_iso = now.isoformat()
    exp_iso = expires.isoformat()

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO demo_sessions (id, token_hash, created_at, expires_at)
    VALUES (?, ?, ?, ?)
    """, (session_id, t_hash, now_iso, exp_iso))

    cursor.execute("""
    INSERT INTO profiles (session_id, daily_minutes, language)
    VALUES (?, 45, 'en')
    """, (session_id,))
    conn.commit()

    response.headers["Cache-Control"] = "no-store"
    # Set HttpOnly Cookie
    response.set_cookie(
        key="pathpilot_session",
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https" or os.getenv("COOKIE_SECURE") == "1",
        max_age=7 * 24 * 3600
    )

    profile = ProfileOut(session_id=session_id, daily_minutes=45, language="en")
    return DemoSessionOut(
        session_id=session_id,
        token=raw_token,
        created_at=now_iso,
        expires_at=exp_iso,
        profile=profile
    )


@router.put("/profile", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdate,
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    cursor = conn.cursor()

    if body.daily_minutes is not None:
        cursor.execute("UPDATE profiles SET daily_minutes = ? WHERE session_id = ?", (body.daily_minutes, session_id))
    if body.language is not None:
        cursor.execute("UPDATE profiles SET language = ? WHERE session_id = ?", (body.language, session_id))
    conn.commit()

    cursor.execute("SELECT daily_minutes, language FROM profiles WHERE session_id = ?", (session_id,))
    p = cursor.fetchone()
    return ProfileOut(session_id=session_id, daily_minutes=p["daily_minutes"], language=p["language"])


# --- 2. Assessments & Grading ---
@router.post("/assessments", response_model=AssessmentOut)
def create_assessment(
    body: AssessmentCreate,
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    if body.kind == "practice" and not body.skill_id:
        raise HTTPException(status_code=422, detail="skill_id is required for practice assessment")
    conn.execute("BEGIN IMMEDIATE")
    try:
        assessment_id = ensure_assessment(
            conn, session["session_id"], body.kind, body.skill_id if body.kind == "practice" else None
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    result = get_assessment(assessment_id, session, conn)
    conn.commit()
    return result


@router.get("/assessments/{id}", response_model=AssessmentOut)
def get_assessment(
    id: str,
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, session_id, kind, skill_id, status, created_at, completed_at
    FROM assessments
    WHERE id = ?
    """, (id,))
    ass = cursor.fetchone()

    if not ass:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if ass["session_id"] != session_id:
        raise HTTPException(status_code=403, detail="Forbidden: Assessment belongs to another session")

    cursor.execute("""
    SELECT ai.id as item_id, ai.ordinal, q.version, q.skill_id, q.purpose, q.stem, q.options_json,
           a.selected_option
    FROM assessment_items ai
    JOIN questions q ON ai.question_id = q.id
    LEFT JOIN answers a ON a.assessment_item_id = ai.id
    WHERE ai.assessment_id = ?
    ORDER BY ai.ordinal ASC
    """, (id,))
    item_rows = cursor.fetchall()

    answered_count = sum(1 for r in item_rows if r["selected_option"] is not None)
    public_items = [
        QuestionPublic(
            id=r["item_id"],
            version=r["version"],
            skill_id=r["skill_id"],
            purpose=r["purpose"],
            stem=r["stem"],
            options=[QuestionOption(**o) for o in json.loads(r["options_json"])],
            ordinal=r["ordinal"]
        ) for r in item_rows
    ]

    return AssessmentOut(
        id=ass["id"],
        session_id=ass["session_id"],
        kind=ass["kind"],
        skill_id=ass["skill_id"],
        status=ass["status"],
        total_items=len(public_items),
        answered_items=answered_count,
        items=public_items,
        created_at=ass["created_at"],
        completed_at=ass["completed_at"]
    )


@router.post("/assessments/{id}/answers", response_model=AnswerResult)
def submit_assessment_answer(
    id: str,
    body: AnswerSubmit,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    cursor = conn.cursor()

    # Ownership check
    cursor.execute("SELECT session_id, kind, skill_id FROM assessments WHERE id = ?", (id,))
    ass = cursor.fetchone()
    if not ass:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if ass["session_id"] != session_id:
        raise HTTPException(status_code=403, detail="Forbidden: Assessment belongs to another session")

    conn.execute("BEGIN IMMEDIATE")
    # Idempotency check
    cached = check_idempotency(conn, session_id, f"/assessments/{id}/answers", idempotency_key, body.model_dump())
    if cached:
        return AnswerResult(**cached)

    # Locate assessment item: body.question_id can be the item_id or question_id
    cursor.execute("""
    SELECT ai.id
    FROM assessment_items ai
    WHERE ai.assessment_id = ? AND ai.id = ?
    """, (id, body.question_id))
    item = cursor.fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="Assessment item not found in this assessment")

    item_id = item["id"]

    existing = conn.execute("SELECT 1 FROM answers WHERE assessment_item_id = ?", (item_id,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="This question already has a saved answer. Reload to continue.")
    next_item = conn.execute("""
        SELECT ai.id FROM assessment_items ai LEFT JOIN answers a ON a.assessment_item_id = ai.id
        WHERE ai.assessment_id = ? AND a.id IS NULL ORDER BY ai.ordinal LIMIT 1
    """, (id,)).fetchone()
    if not next_item or next_item["id"] != item_id:
        raise HTTPException(status_code=409, detail="Answer the current question first.")

    result = submit_answer(conn, item_id, body.selected_option, body.skipped)
    if result.is_completed and ass["kind"] == "practice":
        current = get_current_plan(conn, session_id)
        if current:
            conn.execute("""
                UPDATE tasks SET status = 'completed'
                WHERE plan_id = ? AND kind = 'practice' AND skill_id = ? AND status = 'pending'
            """, (current.id, ass["skill_id"]))
            generate_plan(conn, session_id, current.available_minutes, "Updated after practice", current.version)

    record_idempotency(
        conn, session_id, f"/assessments/{id}/answers", idempotency_key, body.model_dump(), result.model_dump()
    )
    conn.commit()
    return result


@router.get("/assessments/{id}/results", response_model=AssessmentResultOut)
def get_assessment_results(
    id: str,
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    cursor = conn.cursor()

    cursor.execute("SELECT id, session_id, kind, status FROM assessments WHERE id = ?", (id,))
    ass = cursor.fetchone()
    if not ass:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if ass["session_id"] != session_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    cursor.execute("""
    SELECT COUNT(ai.id) as total, COUNT(a.id) as answered
    FROM assessment_items ai
    LEFT JOIN answers a ON a.assessment_item_id = ai.id
    WHERE ai.assessment_id = ?
    """, (id,))
    counts = cursor.fetchone()

    skills = get_skill_evidence(conn, session_id)
    caveats = [
        "Small sample evidence: 3 questions per micro-skill demonstrate immediate diagnostic patterns, not durable exam readiness.",
        "Performance evidence is kept strictly separate between initial diagnostic and subsequent targeted practice."
    ]

    return AssessmentResultOut(
        assessment_id=ass["id"],
        kind=ass["kind"],
        status=ass["status"],
        total_items=counts["total"],
        answered_items=counts["answered"],
        skills=skills,
        caveats=caveats
    )


# --- 3. Progress Overview ---
@router.get("/progress", response_model=ProgressOut)
def get_progress(
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    profile = ProfileOut(
        session_id=session_id,
        daily_minutes=session["daily_minutes"],
        language=session["language"]
    )

    skills = get_skill_evidence(conn, session_id)
    current_plan = get_current_plan(conn, session_id)

    # Check if diagnostic is completed
    cursor = conn.cursor()
    cursor.execute("""
    SELECT status FROM assessments WHERE session_id = ? AND kind = 'diagnostic' AND status = 'completed'
    LIMIT 1
    """, (session_id,))
    diag_completed = cursor.fetchone() is not None

    return ProgressOut(
        session_id=session_id,
        profile=profile,
        skills=skills,
        current_plan=current_plan,
        diagnostic_completed=diag_completed
    )


# --- 4. Study Plans & Replanning ---
@router.post("/plans", response_model=PlanOut)
def create_initial_plan(
    body: PlanCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    conn.execute("BEGIN IMMEDIATE")
    cached = check_idempotency(conn, session_id, "/plans", idempotency_key, body.model_dump())
    if cached:
        return PlanOut(**cached)

    existing = get_current_plan(conn, session_id)
    if existing:
        record_idempotency(conn, session_id, "/plans", idempotency_key, body.model_dump(), existing.model_dump())
        conn.commit()
        return existing
    minutes = body.available_minutes or session["daily_minutes"]
    plan, _, _ = generate_plan(
        conn,
        session_id=session_id,
        available_minutes=minutes,
        reason=body.goal or "Initial recovery study plan"
    )
    conn.execute("UPDATE profiles SET daily_minutes = ? WHERE session_id = ?", (minutes, session_id))
    record_idempotency(conn, session_id, "/plans", idempotency_key, body.model_dump(), plan.model_dump())
    conn.commit()
    return plan


@router.post("/plans/replan", response_model=ReplanResponse)
def replan(
    body: ReplanRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    conn.execute("BEGIN IMMEDIATE")
    cached = check_idempotency(conn, session_id, "/plans/replan", idempotency_key, body.model_dump())
    if cached:
        return ReplanResponse(**cached)

    try:
        plan, deferred, diff = generate_plan(
            conn,
            session_id=session_id,
            available_minutes=body.available_minutes,
            reason=body.reason,
            expected_version=body.expected_version
        )
        conn.execute("UPDATE profiles SET daily_minutes = ? WHERE session_id = ?", (body.available_minutes, session_id))

        response_data = ReplanResponse(
            status="completed",
            action="replan",
            previous_version=diff.previous_version,
            plan_version=plan.version,
            available_minutes=plan.available_minutes,
            scheduled_minutes=plan.scheduled_minutes,
            tasks=plan.tasks,
            deferred_tasks=deferred,
            diff=diff,
            warnings=["Evidence is based on a small sample of diagnostic questions."]
        )

        record_idempotency(conn, session_id, "/plans/replan", idempotency_key, body.model_dump(), response_data.model_dump())
        conn.commit()

        return response_data
    except ConcurrencyConflictError as cce:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "STALE_PLAN_VERSION",
                "message": str(cce),
                "current_version": cce.current_version,
                "expected_version": cce.expected_version,
                "retryable": True
            }
        )


@router.patch("/tasks/{id}", response_model=TaskOut)
def patch_task_status(
    id: str,
    body: TaskStatusUpdate,
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    conn.execute("BEGIN IMMEDIATE")
    try:
        updated = update_task_status(conn, session_id, id, body.status)
        conn.commit()
        return updated
    except ValueError as e:
        conn.rollback()
        raise HTTPException(status_code=404, detail=str(e))


# --- 5. Mentor AI Agent ---
@router.post("/mentor/runs", response_model=AgentRunOut)
def run_mentor(
    body: MentorRunRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    cached = check_idempotency(conn, session_id, "/mentor/runs", idempotency_key, body.model_dump())
    if cached:
        return AgentRunOut(**cached)
    inferred_skill, mode_prefix = mentor_service.infer_concept(body.message)
    conn.execute("BEGIN IMMEDIATE")
    cached = check_idempotency(conn, session_id, "/mentor/runs", idempotency_key, body.model_dump())
    if cached:
        return AgentRunOut(**cached)
    try:
        agent_run = mentor_service.classify_and_execute(
            conn, session_id, body.message, body.expected_plan_version, inferred_skill, mode_prefix
        )
    except ConcurrencyConflictError as exc:
        raise HTTPException(status_code=409, detail={"code": "STALE_PLAN_VERSION", "message": str(exc)}) from exc
    record_idempotency(conn, session_id, "/mentor/runs", idempotency_key, body.model_dump(), agent_run.model_dump())
    conn.commit()
    return agent_run


@router.get("/mentor/runs/{id}", response_model=AgentRunOut)
def get_mentor_run(
    id: str,
    session: Dict[str, Any] = Depends(get_current_session),
    conn: sqlite3.Connection = Depends(get_db)
):
    session_id = session["session_id"]
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, session_id, status, requested_action, user_message, tool_result_json, reply_text, llm_mode, error_code, created_at
    FROM agent_runs
    WHERE id = ?
    """, (id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agent run not found")
    if row["session_id"] != session_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return AgentRunOut(
        run_id=row["id"],
        session_id=row["session_id"],
        status=row["status"],
        requested_action=row["requested_action"],
        tool_result=json.loads(row["tool_result_json"]) if row["tool_result_json"] else None,
        reply_text=row["reply_text"],
        llm_mode=row["llm_mode"],
        error_code=row["error_code"],
        created_at=row["created_at"]
    )


# --- 6. Historical Scenario Comparison ---
@router.post("/scenarios/rank", response_model=ScenarioResultOut)
def scenario_rank(
    body: ScenarioRequest,
    conn: sqlite3.Connection = Depends(get_db)
):
    try:
        result = compare_historical_rank(
            conn=conn,
            rank=body.rank,
            cohort_key=body.cohort_key,
            rank_type=body.rank_type or "CRL"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


# --- 7. Health Check ---
@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "product": "PathPilot Student Recovery Agent",
        "llm_provider_configured": mentor_service.model_configured(),
        "agent_router_configured": bool(mentor_service.agent_router_key),
        "agent_router_model": mentor_service.agent_router_model if mentor_service.agent_router_key else None,
        "database": "sqlite_wal"
    }
