import os
from tempfile import TemporaryDirectory
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sqlite3

# Set test database path before imports
TEST_DB_DIRECTORY = TemporaryDirectory(prefix="pathpilot-pytest-")
TEST_DB_PATH = str(Path(TEST_DB_DIRECTORY.name) / "test_pathpilot.db")
os.environ["SQLITE_DB_PATH"] = TEST_DB_PATH

from backend.app.main import app
from backend.app.db import init_db, get_connection

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    client.cookies.clear()
    # Remove test DB if exists
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
    init_db(TEST_DB_PATH)
    yield
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass


def create_session():
    res = client.post("/api/v1/demo-sessions")
    assert res.status_code == 200
    data = res.json()
    token = data["token"]
    session_id = data["session_id"]
    headers = {"Authorization": f"Bearer {token}", "X-Session-Token": token}
    return session_id, token, headers


# Gate Check 1: Complete the full journey from a fresh session, then reload and confirm persistence.
def test_full_journey_and_persistence():
    session_id, token, headers = create_session()

    # 1. Update daily minutes to 45
    p_res = client.put("/api/v1/profile", json={"daily_minutes": 45}, headers=headers)
    assert p_res.status_code == 200
    assert p_res.json()["daily_minutes"] == 45

    # 2. Start diagnostic (9 questions)
    d_res = client.post("/api/v1/assessments", json={"kind": "diagnostic"}, headers=headers)
    assert d_res.status_code == 200
    diag = d_res.json()
    assert diag["kind"] == "diagnostic"
    assert len(diag["items"]) == 9
    assessment_id = diag["id"]

    # 3. Answer all 9 questions (answering some correctly, some incorrectly to simulate learning gap)
    # Answers:
    # Item 0 (vector_components): diag_vec_comp_1 - Key is B. Choose C (incorrect: component/sign confusion)
    # Item 1 (vector_components): diag_vec_comp_2 - Key is C. Choose C (correct)
    # Item 2 (vector_components): diag_vec_comp_3 - Key is A. Choose B (incorrect)
    # Item 3 (vector_addition): diag_vec_add_1 - Key is B. Choose B (correct)
    # Item 4 (vector_addition): diag_vec_add_2 - Key is D. Choose D (correct)
    # Item 5 (vector_addition): diag_vec_add_3 - Key is C. Choose A (incorrect)
    # Item 6 (constant_accel_1d): diag_mot_1d_1 - Key is A. Choose A (correct)
    # Item 7 (constant_accel_1d): diag_mot_1d_2 - Key is B. Choose B (correct)
    # Item 8 (constant_accel_1d): diag_mot_1d_3 - Key is D. Choose D (correct)
    choices = ["C", "C", "B", "B", "D", "A", "A", "B", "D"]

    for idx, item in enumerate(diag["items"]):
        ans_res = client.post(
            f"/api/v1/assessments/{assessment_id}/answers",
            json={"question_id": item["id"], "selected_option": choices[idx]},
            headers=headers
        )
        assert ans_res.status_code == 200

    # 4. Check assessment results
    r_res = client.get(f"/api/v1/assessments/{assessment_id}/results", headers=headers)
    assert r_res.status_code == 200
    r_data = r_res.json()
    assert r_data["status"] == "completed"
    assert len(r_data["skills"]) == 3

    # Vector components should have 1 correct out of 3
    vec_comp = next(s for s in r_data["skills"] if s["skill_id"] == "vector_components")
    assert vec_comp["diagnostic_correct"] == 1
    assert vec_comp["diagnostic_attempted"] == 3
    assert vec_comp["status"] == "needs_practice"
    assert "Small sample" in vec_comp["evidence_caveat"]

    # 5. Generate initial study plan
    plan_res = client.post("/api/v1/plans", json={"available_minutes": 45}, headers=headers)
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert plan_data["version"] == 1
    assert plan_data["scheduled_minutes"] <= 45
    assert len(plan_data["tasks"]) > 0

    # 6. Verify persistence across fresh request ("reload")
    prog_res = client.get("/api/v1/progress", headers=headers)
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["diagnostic_completed"] is True
    assert prog_data["current_plan"]["version"] == 1
    assert prog_data["current_plan"]["scheduled_minutes"] == plan_data["scheduled_minutes"]


# Gate Check 2: Submit one answer twice and verify only one record and one update exist.
def test_idempotent_answer_submission():
    session_id, token, headers = create_session()

    d_res = client.post("/api/v1/assessments", json={"kind": "diagnostic"}, headers=headers)
    assessment_id = d_res.json()["id"]
    first_item = d_res.json()["items"][0]

    # First submission with Idempotency-Key
    idemp_headers = {**headers, "Idempotency-Key": "test-key-12345"}
    payload = {"question_id": first_item["id"], "selected_option": "B"}

    res1 = client.post(f"/api/v1/assessments/{assessment_id}/answers", json=payload, headers=idemp_headers)
    assert res1.status_code == 200
    ans1 = res1.json()

    # Second submission with exact same key and payload
    res2 = client.post(f"/api/v1/assessments/{assessment_id}/answers", json=payload, headers=idemp_headers)
    assert res2.status_code == 200
    ans2 = res2.json()

    assert ans1["answer_id"] == ans2["answer_id"]
    assert ans1["correctness"] == ans2["correctness"]

    # Verify directly in SQLite that only 1 answer row exists
    conn = get_connection(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM answers WHERE assessment_item_id = ?", (first_item["id"],))
    count = cursor.fetchone()["count"]
    conn.close()
    assert count == 1


# Gate Check 3: Attempt to fetch another session's assessment or plan; access must fail.
def test_session_isolation_and_authorization():
    # Session A
    session_a, token_a, headers_a = create_session()
    d_res_a = client.post("/api/v1/assessments", json={"kind": "diagnostic"}, headers=headers_a)
    assessment_id_a = d_res_a.json()["id"]

    # Session B
    session_b, token_b, headers_b = create_session()

    # Session B attempts to access Session A's assessment
    unauth_get = client.get(f"/api/v1/assessments/{assessment_id_a}", headers=headers_b)
    assert unauth_get.status_code in [403, 404]

    # Session B attempts to answer Session A's assessment
    unauth_post = client.post(
        f"/api/v1/assessments/{assessment_id_a}/answers",
        json={"question_id": d_res_a.json()["items"][0]["id"], "selected_option": "B"},
        headers=headers_b
    )
    assert unauth_post.status_code in [403, 404]

    # Missing token (clear cookies on test client first)
    client.cookies.clear()
    no_token = client.get(f"/api/v1/assessments/{assessment_id_a}")
    assert no_token.status_code == 401


# Gate Check 4: Ask for a 30-minute plan; verify the sum, saved version and visible change.
def test_replan_via_mentor_and_plan_sum():
    session_id, token, headers = create_session()

    # Seed initial plan (version 1)
    client.post("/api/v1/plans", json={"available_minutes": 60}, headers=headers)

    # Replan to 30 minutes via Mentor request
    mentor_res = client.post(
        "/api/v1/mentor/runs",
        json={"message": "I only have 30 minutes today", "expected_plan_version": 1},
        headers=headers
    )
    assert mentor_res.status_code == 200
    run_data = mentor_res.json()
    assert run_data["requested_action"] == "replan"
    tool_res = run_data["tool_result"]
    assert tool_res is not None
    assert tool_res["plan_version"] == 2
    assert tool_res["available_minutes"] == 30
    assert tool_res["scheduled_minutes"] <= 30
    assert sum(t["minutes"] for t in tool_res["tasks"]) == tool_res["scheduled_minutes"]
    assert len(tool_res["deferred_tasks"]) > 0

    # Verify persisted plan version in database
    prog = client.get("/api/v1/progress", headers=headers).json()
    assert prog["current_plan"]["version"] == 2
    assert prog["current_plan"]["available_minutes"] == 30


# Gate Check 5: Complete a task; verify that correctness counts do not increase without a quiz.
def test_complete_task_does_not_increase_quiz_score():
    session_id, token, headers = create_session()

    # Diagnostic with 1 correct
    d_res = client.post("/api/v1/assessments", json={"kind": "diagnostic"}, headers=headers)
    ass_id = d_res.json()["id"]
    # Answer first question correctly
    client.post(
        f"/api/v1/assessments/{ass_id}/answers",
        json={"question_id": d_res.json()["items"][0]["id"], "selected_option": "B"},
        headers=headers
    )

    # Initial evidence check
    ev1 = client.get("/api/v1/progress", headers=headers).json()["skills"]
    vec_comp_ev1 = next(s for s in ev1 if s["skill_id"] == "vector_components")
    initial_correct = vec_comp_ev1["diagnostic_correct"]
    assert initial_correct == 1

    # Create plan and complete a task
    plan = client.post("/api/v1/plans", json={"available_minutes": 30}, headers=headers).json()
    first_task = plan["tasks"][0]

    patch_res = client.patch(
        f"/api/v1/tasks/{first_task['id']}",
        json={"status": "completed"},
        headers=headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"

    # Evidence check after completing task: quiz correctness count MUST NOT change!
    ev2 = client.get("/api/v1/progress", headers=headers).json()["skills"]
    vec_comp_ev2 = next(s for s in ev2 if s["skill_id"] == "vector_components")
    assert vec_comp_ev2["diagnostic_correct"] == initial_correct
    assert vec_comp_ev2["practice_correct"] == 0  # no practice quiz was taken


# Gate Check 6: Submit a fresh practice answer; verify the right skill updates and earlier records remain.
def test_fresh_practice_updates_separately():
    session_id, token, headers = create_session()

    # Diagnostic
    d_res = client.post("/api/v1/assessments", json={"kind": "diagnostic"}, headers=headers)
    ass_id = d_res.json()["id"]
    # Answer 1 diagnostic question
    client.post(
        f"/api/v1/assessments/{ass_id}/answers",
        json={"question_id": d_res.json()["items"][0]["id"], "selected_option": "B"},
        headers=headers
    )

    # Start fresh practice for vector_components
    prac_res = client.post("/api/v1/assessments", json={"kind": "practice", "skill_id": "vector_components"}, headers=headers)
    assert prac_res.status_code == 200
    prac_ass = prac_res.json()
    assert prac_ass["kind"] == "practice"
    assert len(prac_ass["items"]) == 3

    # Answer practice question 1 (key is C)
    p_ans = client.post(
        f"/api/v1/assessments/{prac_ass['id']}/answers",
        json={"question_id": prac_ass["items"][0]["id"], "selected_option": "C"},
        headers=headers
    )
    assert p_ans.status_code == 200
    assert p_ans.json()["correctness"] is True

    # Check progress: diagnostic count is preserved, practice count is updated
    prog = client.get("/api/v1/progress", headers=headers).json()
    vc = next(s for s in prog["skills"] if s["skill_id"] == "vector_components")
    assert vc["diagnostic_correct"] == 1
    assert vc["practice_correct"] == 1
    assert vc["practice_attempted"] == 1


# Gate Check 7: Disable/fail the LLM call; diagnostic/planning still work and UI describes failure truthfully.
def test_mentor_offline_fallback():
    session_id, token, headers = create_session()

    # Call mentor without any external LLM configured
    res = client.post(
        "/api/v1/mentor/runs",
        json={"message": "explain vector components"},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["requested_action"] == "explain_skill"
    assert "Deterministic Engine" in data["llm_mode"]
    assert "Vector Components & Decomposition" in data["reply_text"]


# Gate Check 8: Use an incompatible rank type or missing source row; return unsupported/unavailable.
def test_scenario_rank_validation():
    # 1. Valid rank comparison against JoSAA 2024
    valid_res = client.post(
        "/api/v1/scenarios/rank",
        json={"rank": 1224, "cohort_key": "nitt_crl_open_os_2024", "rank_type": "CRL"}
    )
    assert valid_res.status_code == 200
    v_data = valid_res.json()
    assert len(v_data["rows"]) == 3
    # CSE closes at 1224; an equal rank meets the threshold.
    nitt = next(r for r in v_data["rows"] if r["program"].startswith("Computer Science"))
    assert nitt["status"] == "at_or_better"

    # 2. Incompatible rank type (Category OBC instead of CRL)
    incompat_res = client.post(
        "/api/v1/scenarios/rank",
        json={"rank": 500, "cohort_key": "nitt_crl_open_os_2024", "rank_type": "OBC_NCL"}
    )
    assert incompat_res.status_code == 422
    assert "Incompatible rank type" in incompat_res.json()["detail"]

    # 3. Non-existent cohort
    missing_cohort = client.post(
        "/api/v1/scenarios/rank",
        json={"rank": 1500, "cohort_key": "non_existent_cohort", "rank_type": "CRL"}
    )
    assert missing_cohort.status_code == 422
    assert "Unsupported scenario" in missing_cohort.json()["detail"]


# Concurrency Check: Stale expected_version should return 409 Conflict
def test_stale_plan_version_conflict():
    session_id, token, headers = create_session()

    # Create plan 1
    p1 = client.post("/api/v1/plans", json={"available_minutes": 45}, headers=headers).json()
    assert p1["version"] == 1

    # Replan with wrong expected_version (e.g. 99)
    bad_replan = client.post(
        "/api/v1/plans/replan",
        json={"available_minutes": 30, "expected_version": 99},
        headers=headers
    )
    assert bad_replan.status_code == 409
    assert bad_replan.json()["detail"]["code"] == "STALE_PLAN_VERSION"


def test_assessments_resume_and_do_not_count_replays():
    _, _, headers = create_session()
    start = lambda kind, **fields: client.post(
        "/api/v1/assessments", json={"kind": kind, **fields}, headers=headers
    ).json()
    diagnostic = start("diagnostic")
    path = f"/api/v1/assessments/{diagnostic['id']}/answers"
    items = diagnostic["items"]
    assert client.post(path, headers=headers, json={"question_id": items[1]["id"], "selected_option": "A"}).status_code == 409
    saved = client.post(path, headers=headers, json={"question_id": items[0]["id"], "selected_option": "B"})
    assert saved.json()["next_question_id"] == items[1]["id"]
    resumed = start("diagnostic")
    assert (resumed["id"], resumed["answered_items"]) == (diagnostic["id"], 1)
    assert client.post(path, headers=headers, json={"question_id": items[0]["id"], "selected_option": "A"}).status_code == 409

    practice = start("practice", skill_id="vector_components")
    launched = client.post("/api/v1/mentor/runs", headers=headers, json={"message": "Start practice on vector components"})
    assert launched.json()["tool_result"]["assessment_id"] == practice["id"]


def test_mentor_preview_replay_and_saved_plan_diff():
    _, _, headers = create_session()
    plan = client.post("/api/v1/plans", headers=headers, json={"available_minutes": 60}).json()
    url = "/api/v1/mentor/runs"
    for message in ("What if I only had 30 minutes?", "Explain constant acceleration in 30 minutes", "Do not replan to 30 minutes"):
        client.post(url, headers=headers, json={"message": message, "expected_plan_version": plan["version"]})
        assert client.get("/api/v1/progress", headers=headers).json()["current_plan"]["version"] == plan["version"]

    request = {"message": "I only have 30 minutes today", "expected_plan_version": plan["version"]}
    replay_headers = {**headers, "Idempotency-Key": "replan-once"}
    first = client.post(url, headers=replay_headers, json=request)
    assert first.status_code == 200, first.text
    result = first.json()["tool_result"]
    assert result["diff"]["minutes_diff"] < 0
    assert result["diff"]["removed_tasks"]
    assert result["deferred_tasks"]
    assert client.post(url, headers=replay_headers, json=request).json() == first.json()
    assert client.post(url, headers=headers, json=request).status_code == 409
    progress = client.get("/api/v1/progress", headers=headers).json()
    assert progress["profile"]["daily_minutes"] == 30
    assert progress["current_plan"]["deferred_tasks"] == result["deferred_tasks"]


def test_practice_completion_replans_once():
    _, _, headers = create_session()
    plan = client.post("/api/v1/plans", headers=headers, json={"available_minutes": 45}).json()
    practice = client.post(
        "/api/v1/assessments", headers=headers, json={"kind": "practice", "skill_id": "vector_components"}
    ).json()
    for item, option in zip(practice["items"], ["C", "A", "B"]):
        payload = {"question_id": item["id"], "selected_option": option}
        answer_headers = {**headers, "Idempotency-Key": item["id"]}
        url = f"/api/v1/assessments/{practice['id']}/answers"
        assert client.post(url, headers=answer_headers, json=payload).status_code == 200
        assert client.post(url, headers=answer_headers, json=payload).status_code == 200
    progress = client.get("/api/v1/progress", headers=headers).json()
    assert progress["current_plan"]["version"] == plan["version"] + 1
    assert progress["skills"][0]["practice_correct"] == 3
    assert progress["skills"][0]["diagnostic_attempted"] == 0


def test_expired_session_and_cross_origin_writes():
    session_id, _, headers = create_session()
    conn = get_connection(TEST_DB_PATH)
    try:
        conn.execute("UPDATE demo_sessions SET expires_at = '2020-01-01T00:00:00+00:00' WHERE id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()
    assert client.get("/api/v1/progress", headers=headers).status_code == 401
    assert client.post("/api/v1/demo-sessions", headers={"Origin": "https://unrelated.example"}).status_code == 403


def test_model_routing_uses_reviewed_notes_and_falls_back(monkeypatch):
    import httpx
    _, _, headers = create_session()
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    monkeypatch.setenv("GEMINI_MODEL", "configured-model")
    calls = []

    def topic_response(url, **kwargs):
        calls.append(url)
        return httpx.Response(200, request=httpx.Request("POST", url), json={
            "candidates": [{"content": {"parts": [{"text": "constant_accel_1d"}]}}]
        })

    monkeypatch.setattr(httpx, "post", topic_response)
    url = "/api/v1/mentor/runs"
    response = client.post(url, headers=headers, json={"message": "Why does an accelerating car get faster?"}).json()
    assert response["llm_mode"].startswith("Deterministic")  # explicit acceleration bypasses provider
    assert not calls
    response = client.post(url, headers=headers, json={"message": "Why does a falling object get faster?"}).json()
    assert response["llm_mode"].startswith("Gemini")
    assert response["tool_result"]["note"]["skill_id"] == "constant_accel_1d"
    assert len(calls) == 1

    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout("test timeout")

    monkeypatch.setattr(httpx, "post", timeout)
    response = client.post(url, headers=headers, json={"message": "Why does a falling object get faster?"}).json()
    assert response["llm_mode"].startswith("Deterministic")
    assert response["requested_action"] == "get_progress"
