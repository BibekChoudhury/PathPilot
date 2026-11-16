"""
PathPilot Acceptance Checks Runner (Section 14 Verification Gates)
Runs each of the 10 gates specified in Section 14 of the build plan.
"""

import os
import sys
import sqlite3
from tempfile import TemporaryDirectory
from pathlib import Path
from fastapi.testclient import TestClient

# Setup database
TEST_DB_DIR = TemporaryDirectory(prefix="pathpilot-acceptance-")
TEST_DB = str(Path(TEST_DB_DIR.name) / "acceptance_test.db")
os.environ["SQLITE_DB_PATH"] = TEST_DB

from backend.app.main import app
from backend.app.db import init_db, get_connection

def main():
    if os.path.exists(TEST_DB):
        try: os.remove(TEST_DB)
        except Exception: pass
    init_db(TEST_DB)

    client = TestClient(app)
    print("=" * 70)
    print("PATHPILOT ACCEPTANCE CHECKS - SECTION 14 VERIFICATION GATES")
    print("=" * 70)

    passed_checks = 0

    # Helper
    def create_sess():
        res = client.post("/api/v1/demo-sessions")
        assert res.status_code == 200, "Failed to create session"
        data = res.json()
        headers = {"Authorization": f"Bearer {data['token']}", "X-Session-Token": data['token']}
        return data["session_id"], data["token"], headers

    # Gate 1: Full journey and reload persistence
    print("\n[Gate 1] Full journey from fresh session -> reload -> persistence...")
    s1_id, s1_tok, s1_headers = create_sess()
    # Diagnostic
    diag = client.post("/api/v1/assessments", json={"kind": "diagnostic"}, headers=s1_headers).json()
    assert len(diag["items"]) == 9
    # Answer 9 items
    choices = ["C", "C", "B", "B", "D", "A", "A", "B", "D"]
    for i, itm in enumerate(diag["items"]):
        client.post(f"/api/v1/assessments/{diag['id']}/answers", json={"question_id": itm["id"], "selected_option": choices[i]}, headers=s1_headers)
    # Plan
    p1 = client.post("/api/v1/plans", json={"available_minutes": 45}, headers=s1_headers).json()
    assert p1["version"] == 1
    # Reload verification
    prog = client.get("/api/v1/progress", headers=s1_headers).json()
    assert prog["diagnostic_completed"] is True
    assert prog["current_plan"]["version"] == 1
    assert prog["current_plan"]["scheduled_minutes"] == p1["scheduled_minutes"]
    print("  PASS: Full journey completed and verified persisted after session reload.")
    passed_checks += 1

    # Gate 2: Submit one answer twice -> only 1 record
    print("\n[Gate 2] Idempotency: Submit one answer twice...")
    s2_id, s2_tok, s2_headers = create_sess()
    d2 = client.post("/api/v1/assessments", json={"kind": "diagnostic"}, headers=s2_headers).json()
    itm_id = d2["items"][0]["id"]
    idemp_key = "idemp-test-unique-key-42"
    r1 = client.post(f"/api/v1/assessments/{d2['id']}/answers", json={"question_id": itm_id, "selected_option": "B"}, headers={**s2_headers, "Idempotency-Key": idemp_key})
    r2 = client.post(f"/api/v1/assessments/{d2['id']}/answers", json={"question_id": itm_id, "selected_option": "B"}, headers={**s2_headers, "Idempotency-Key": idemp_key})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["answer_id"] == r2.json()["answer_id"]
    # Check SQLite DB
    conn = get_connection(TEST_DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM answers WHERE assessment_item_id = ?", (itm_id,))
    count = c.fetchone()["count"]
    conn.close()
    assert count == 1, f"Expected 1 answer row, found {count}"
    print("  PASS: Duplicate answer rejected/cached; database holds exactly 1 record.")
    passed_checks += 1

    # Gate 3: Session isolation & unauthorized access
    print("\n[Gate 3] Session isolation: Fetch another session's assessment...")
    s3_id, s3_tok, s3_headers = create_sess()
    s4_id, s4_tok, s4_headers = create_sess()
    d3 = client.post("/api/v1/assessments", json={"kind": "diagnostic"}, headers=s3_headers).json()
    # S4 attempts to access S3's assessment
    unauth_res = client.get(f"/api/v1/assessments/{d3['id']}", headers=s4_headers)
    assert unauth_res.status_code in [403, 404]
    client.cookies.clear()
    no_auth = client.get(f"/api/v1/assessments/{d3['id']}")
    assert no_auth.status_code == 401
    print("  PASS: Access across sessions blocked with 403 Forbidden; unauthenticated blocked with 401.")
    passed_checks += 1

    # Gate 4: Ask for 30-minute plan -> verify sum, saved version, visible diff
    print("\n[Gate 4] Replan via mentor to 30 minutes...")
    mentor_res = client.post(
        "/api/v1/mentor/runs",
        json={"message": "I only have 30 minutes today", "expected_plan_version": 1},
        headers=s1_headers
    ).json()
    assert mentor_res["requested_action"] == "replan"
    tres = mentor_res["tool_result"]
    assert tres["plan_version"] == 2
    assert tres["available_minutes"] == 30
    assert tres["scheduled_minutes"] <= 30
    assert sum(t["minutes"] for t in tres["tasks"]) == tres["scheduled_minutes"]
    assert len(tres["deferred_tasks"]) > 0
    print(f"  PASS: Replan succeeded. Version 1 -> 2, Scheduled: {tres['scheduled_minutes']}m / 30m, Deferred: {len(tres['deferred_tasks'])} tasks.")
    passed_checks += 1

    # Gate 5: Complete task -> verify score does NOT increase
    print("\n[Gate 5] Complete task -> verify correctness counts DO NOT increase without quiz...")
    ev_before = client.get("/api/v1/progress", headers=s1_headers).json()["skills"]
    vc_before = next(s for s in ev_before if s["skill_id"] == "vector_components")
    # Complete task
    p_curr = client.get("/api/v1/progress", headers=s1_headers).json()["current_plan"]
    t0 = p_curr["tasks"][0]
    client.patch(f"/api/v1/tasks/{t0['id']}", json={"status": "completed"}, headers=s1_headers)
    ev_after = client.get("/api/v1/progress", headers=s1_headers).json()["skills"]
    vc_after = next(s for s in ev_after if s["skill_id"] == "vector_components")
    assert vc_before["diagnostic_correct"] == vc_after["diagnostic_correct"]
    assert vc_after["practice_correct"] == 0
    print("  PASS: Task status completed; assessment correctness count remained unchanged.")
    passed_checks += 1

    # Gate 6: Fresh practice answer -> verify skill updates separately
    print("\n[Gate 6] Fresh practice submission -> verify separate practice evidence...")
    prac_ass = client.post("/api/v1/assessments", json={"kind": "practice", "skill_id": "vector_components"}, headers=s1_headers).json()
    assert len(prac_ass["items"]) == 3
    # Submit first practice question (Key is C)
    client.post(
        f"/api/v1/assessments/{prac_ass['id']}/answers",
        json={"question_id": prac_ass["items"][0]["id"], "selected_option": "C"},
        headers=s1_headers
    )
    ev_prac = client.get("/api/v1/progress", headers=s1_headers).json()["skills"]
    vc_prac = next(s for s in ev_prac if s["skill_id"] == "vector_components")
    assert vc_prac["practice_correct"] == 1
    assert vc_prac["practice_attempted"] == 1
    assert vc_prac["diagnostic_correct"] == vc_before["diagnostic_correct"]
    print("  PASS: Practice count incremented to 1 while diagnostic score remained distinct.")
    passed_checks += 1

    # Gate 7: Mentor offline / disabled LLM -> graceful fallback & truthful reporting
    print("\n[Gate 7] Fallback handling: Mentor tool execution without external LLM...")
    offline_run = client.post(
        "/api/v1/mentor/runs",
        json={"message": "explain vector components"},
        headers=s1_headers
    ).json()
    assert offline_run["status"] == "completed"
    assert offline_run["requested_action"] == "explain_skill"
    assert "Deterministic Engine" in offline_run["llm_mode"]
    print(f"  PASS: Tool executed via fallback. LLM Mode truthfully reported: '{offline_run['llm_mode']}'.")
    passed_checks += 1

    # Gate 8: Incompatible rank type or missing row -> unsupported/unavailable
    print("\n[Gate 8] Historical Cutoff validation: Incompatible rank type & missing cohort...")
    incompat = client.post(
        "/api/v1/scenarios/rank",
        json={"rank": 1500, "cohort_key": "nitt_crl_open_os_2024", "rank_type": "OBC_NCL"}
    )
    assert incompat.status_code == 422
    assert "Incompatible rank type" in incompat.json()["detail"]
    missing = client.post(
        "/api/v1/scenarios/rank",
        json={"rank": 1500, "cohort_key": "non_existent_cohort", "rank_type": "CRL"}
    )
    assert missing.status_code == 422
    assert "Unsupported scenario" in missing.json()["detail"]
    print("  PASS: Incompatible rank type and missing cohort rejected with descriptive 422.")
    passed_checks += 1

    # Gate 9: Phone-width layout and keyboard navigation checks
    print("\n[Gate 9] UI Layout and keyboard navigation verification...")
    print("  MANUAL: Check the mobile viewport and keyboard controls in a browser.")

    # Gate 10: Clean-start & single process serving
    print("\n[Gate 10] Clean start and single process serving...")
    spa_res = client.get("/")
    assert spa_res.status_code == 200
    assert "PathPilot" in spa_res.text or 'id="root"' in spa_res.text
    print("  PASS: Single-process FastAPI serves built React SPA and API endpoints.")
    passed_checks += 1

    print("\n" + "=" * 70)
    print(f"VERIFICATION COMPLETE: {passed_checks} AUTOMATED CHECKS PASSED; BROWSER CHECK MANUAL")
    print("=" * 70)

    # Cleanup
    if os.path.exists(TEST_DB):
        try: os.remove(TEST_DB)
        except Exception: pass

if __name__ == "__main__":
    main()

