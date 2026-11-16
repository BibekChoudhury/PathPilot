import os
import re
import json
import uuid
import httpx
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import sqlite3
from dotenv import load_dotenv

from ..schemas import AgentRunOut

BASE_DIR = Path(__file__).resolve().parents[2]  # backend directory
DATA_DIR = BASE_DIR / "data"

load_dotenv()


def load_notes_dict() -> Dict[str, Dict[str, Any]]:
    notes_path = DATA_DIR / "notes.json"
    if not notes_path.exists():
        return {}
    with open(notes_path, "r", encoding="utf-8") as f:
        notes = json.load(f)
        return {n["skill_id"]: n for n in notes}


class MentorService:
    def __init__(self):
        self.agent_router_key = os.environ.get("AGENT_ROUTER_KEY")
        self.agent_router_model = os.environ.get("AGENT_ROUTER_MODEL", "gpt-6-astra")
        self.agent_router_base_url = os.environ.get("AGENT_ROUTER_BASE_URL", "https://api.openai.com/v1")
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")

    def model_configured(self) -> bool:
        return bool(self.agent_router_key or self.gemini_api_key or self.openai_api_key)

    def infer_concept(self, message: str) -> Tuple[Optional[str], str]:
        """
        Infers the target micro-skill from a student query.
        Returns (skill_id or None, mode_prefix).
        """
        msg_lower = message.strip().lower()

        # Deterministic rule checks: explicit physical terms bypass provider
        if any(w in msg_lower for w in ["accelerat", "car", "stop", "brake", "kinematic", "1d motion"]):
            return "constant_accel_1d", "Deterministic"
        if any(w in msg_lower for w in ["component", "decompose", "horizontal", "vertical", "quadrant"]):
            return "vector_components", "Deterministic"
        if any(w in msg_lower for w in ["addition", "resultant", "add vector", "parallelogram"]):
            return "vector_addition", "Deterministic"

        # Check Gemini API if configured
        gemini_key = os.environ.get("GEMINI_API_KEY") or self.gemini_api_key
        gemini_model = os.environ.get("GEMINI_MODEL") or self.gemini_model
        if gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
            try:
                resp = httpx.post(url, json={
                    "contents": [{"parts": [{"text": f"Classify into one skill (constant_accel_1d, vector_components, vector_addition): {message}"}]}]
                }, timeout=4.0)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    for skill in ["constant_accel_1d", "vector_components", "vector_addition"]:
                        if skill in raw_text:
                            return skill, "Gemini"
            except Exception:
                return None, "Deterministic"

        # Check Agent Router if configured
        router_key = os.environ.get("AGENT_ROUTER_KEY") or self.agent_router_key
        if router_key:
            endpoint = f"{self.agent_router_base_url.rstrip('/')}/chat/completions"
            headers = {"Authorization": f"Bearer {router_key}", "Content-Type": "application/json"}
            payload = {
                "model": os.environ.get("AGENT_ROUTER_MODEL") or self.agent_router_model,
                "messages": [{"role": "user", "content": f"Classify into one skill (constant_accel_1d, vector_components, vector_addition): {message}"}],
                "max_tokens": 50
            }
            try:
                with httpx.Client(timeout=4.0) as client:
                    resp = client.post(endpoint, headers=headers, json=payload)
                    if resp.status_code == 200:
                        text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                        for skill in ["constant_accel_1d", "vector_components", "vector_addition"]:
                            if skill in text:
                                return skill, f"Agent Router ({self.agent_router_model})"
            except Exception:
                return None, "Deterministic"

        return None, "Deterministic"

    def execute_tool(
        self,
        conn: sqlite3.Connection,
        session_id: str,
        tool_name: str,
        args: Dict[str, Any],
        expected_version: Optional[int] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Executes an allowlisted backend service tool with server-enforced session authorization.
        """
        if tool_name == "get_progress":
            from .grading import get_skill_evidence
            from .planner import get_current_plan
            evidence = get_skill_evidence(conn, session_id)
            current_plan = get_current_plan(conn, session_id)
            result = {
                "evidence": [e.model_dump() for e in evidence],
                "plan": current_plan.model_dump() if current_plan else None
            }
            summary = "Retrieved authenticated session progress and active study plan."
            return result, summary

        elif tool_name == "explain_skill":
            skill_id = args.get("skill_id", "vector_components")
            notes = load_notes_dict()
            note = notes.get(skill_id)
            if not note:
                return {"error": f"Skill '{skill_id}' not found in reviewed notes."}, "Skill not found."
            return {"note": note}, f"Loaded verified concept guide for {note['title']}."

        elif tool_name == "start_practice":
            skill_id = args.get("skill_id", "vector_components")
            cursor = conn.cursor()

            # Check if an in-progress practice assessment already exists for this skill
            cursor.execute("""
            SELECT id FROM assessments
            WHERE session_id = ? AND kind = 'practice' AND skill_id = ? AND status != 'completed'
            ORDER BY created_at DESC LIMIT 1
            """, (session_id, skill_id))
            existing_ass = cursor.fetchone()

            if existing_ass:
                return {
                    "assessment_id": existing_ass["id"],
                    "skill_id": skill_id,
                    "total_items": 3,
                    "status": "in_progress"
                }, f"Resumed active practice session for {skill_id}."

            # Otherwise create a new one
            cursor.execute("""
            SELECT id FROM questions
            WHERE skill_id = ? AND purpose = 'practice'
            ORDER BY id ASC
            LIMIT 3
            """, (skill_id,))
            questions = cursor.fetchall()
            if not questions:
                return {"error": f"No practice questions available for '{skill_id}'."}, "No practice questions."

            now_iso = datetime.now(timezone.utc).isoformat()
            assessment_id = f"ass_prac_{uuid.uuid4().hex[:10]}"
            cursor.execute("""
            INSERT INTO assessments (id, session_id, kind, skill_id, status, created_at)
            VALUES (?, ?, 'practice', ?, 'in_progress', ?)
            """, (assessment_id, session_id, skill_id, now_iso))

            items = []
            for idx, q in enumerate(questions):
                item_id = f"item_{uuid.uuid4().hex[:10]}"
                cursor.execute("""
                INSERT INTO assessment_items (id, assessment_id, question_id, ordinal)
                VALUES (?, ?, ?, ?)
                """, (item_id, assessment_id, q["id"], idx))
                items.append({"item_id": item_id, "question_id": q["id"]})

            conn.commit()
            return {
                "assessment_id": assessment_id,
                "skill_id": skill_id,
                "total_items": len(items),
                "status": "in_progress"
            }, f"Launched fresh 3-question practice session for {skill_id}."

        elif tool_name == "replan":
            from .planner import get_current_plan, generate_plan
            minutes = args.get("available_minutes", 30)
            reason = args.get("reason", "Adjusted daily study budget")
            current = get_current_plan(conn, session_id)
            cur_ver = current.version if current else 0
            target_expected_ver = expected_version if expected_version is not None else cur_ver

            plan, deferred, diff = generate_plan(
                conn,
                session_id=session_id,
                available_minutes=minutes,
                reason=reason,
                expected_version=target_expected_ver
            )
            conn.execute("UPDATE profiles SET daily_minutes = ? WHERE session_id = ?", (minutes, session_id))
            conn.commit()

            result = {
                "status": "completed",
                "action": "replan",
                "previous_version": diff.previous_version,
                "plan_version": plan.version,
                "available_minutes": plan.available_minutes,
                "scheduled_minutes": plan.scheduled_minutes,
                "tasks": [t.model_dump() for t in plan.tasks],
                "deferred_tasks": [d.model_dump() for d in deferred],
                "diff": diff.model_dump(),
                "warnings": ["Small sample evidence: plan addresses primary diagnostic weakness."]
            }
            summary = (
                f"Successfully replanned today's schedule for {minutes} minutes (version {plan.version}). "
                f"Scheduled {plan.scheduled_minutes} minutes across {len(plan.tasks)} tasks. "
                f"{len(deferred)} tasks were explicitly deferred."
            )
            return result, summary

        elif tool_name == "compare_rank":
            from .scenarios import compare_historical_rank
            rank = args.get("rank", 1224)
            cohort_key = args.get("cohort_key", "nitt_crl_open_os_2024")
            rank_type = args.get("rank_type", "CRL")
            scenario_res = compare_historical_rank(conn, rank=rank, cohort_key=cohort_key, rank_type=rank_type)
            result = scenario_res.model_dump()
            summary = (
                f"Historical JoSAA 2024 comparison for CRL {rank}: "
                f"{sum(1 for r in scenario_res.rows if r.status == 'at_or_better')} of {len(scenario_res.rows)} "
                f"programs met historical closing rank threshold."
            )
            return result, summary

        else:
            return {"error": f"Tool '{tool_name}' is not allowed or unrecognized."}, "Tool execution denied."

    def classify_and_execute(
        self,
        conn: sqlite3.Connection,
        session_id: str,
        message: str,
        expected_plan_version: Optional[int] = None,
        inferred_skill: Optional[str] = None,
        mode_prefix: Optional[str] = None
    ) -> AgentRunOut:
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        msg_lower = message.strip().lower()

        # Check explicit keywords
        minute_match = re.search(r"(\b\d{1,3}\b)\s*(?:min|mins|minutes)", msg_lower)
        is_preview = any(kw in msg_lower for kw in ["what if", "preview", "hypothetical"])
        is_negated = any(kw in msg_lower for kw in ["do not", "don't", "dont", "never"])
        is_explain_query = any(w in msg_lower for w in ["explain", "why", "how", "what is", "help with", "notes", "concept"])

        # Determine skill if not provided
        if inferred_skill is None and mode_prefix is None:
            inferred_skill, mode_prefix = self.infer_concept(message)
        elif mode_prefix is None:
            _, mode_prefix = self.infer_concept(message)

        requested_action = "none"
        tool_result = None
        reply_text = ""

        # 1. Replan Intent (Must NOT be preview, explanation, or negated!)
        if minute_match and not is_preview and not is_explain_query and not is_negated and any(w in msg_lower for w in ["i only have", "make today", "replan", "adjust", "reschedule", "change my plan"]):
            requested_action = "replan"
            target_mins = int(minute_match.group(1)) if minute_match else 30
            target_mins = max(15, min(240, target_mins))

            tool_res, summary = self.execute_tool(
                conn,
                session_id,
                tool_name="replan",
                args={"available_minutes": target_mins, "reason": f"Student request: '{message}'"},
                expected_version=expected_plan_version
            )
            tool_result = tool_res
            reply_text = (
                f"I have updated your study plan to fit your {target_mins}-minute window. "
                f"Your new plan (version {tool_res['plan_version']}) allocates {tool_res['scheduled_minutes']} minutes. "
                f"Tasks that cannot fit are explicitly deferred so no goals are silently dropped."
            )

        # 2. Preview Intent
        elif is_preview or (minute_match and is_negated):
            requested_action = "preview_replan"
            target_mins = int(minute_match.group(1)) if minute_match else 30
            reply_text = (
                f"PREVIEW: If you adjust your daily budget to {target_mins} minutes, "
                f"PathPilot will prioritize your weakest diagnostic skill (10 min learn + 15 min practice) "
                f"and defer non-critical blocks. Reply 'Make today's plan {target_mins} minutes' to apply this change."
            )
            tool_result = {
                "preview_minutes": target_mins,
                "action_required": "confirm_to_apply"
            }

        # 3. Rank Comparison Intent
        elif "rank" in msg_lower or "nit" in msg_lower or "josaa" in msg_lower or "college" in msg_lower:
            requested_action = "compare_rank"
            rank_match = re.search(r"\b(\d{2,6})\b", msg_lower)
            rank_val = int(rank_match.group(1)) if rank_match else 1224

            tool_res, summary = self.execute_tool(
                conn,
                session_id,
                tool_name="compare_rank",
                args={"rank": rank_val, "cohort_key": "nitt_crl_open_os_2024", "rank_type": "CRL"}
            )
            tool_result = tool_res
            reply_text = summary

        # 4. Start Practice Intent
        elif "practice" in msg_lower or "test me" in msg_lower or "quiz" in msg_lower:
            requested_action = "start_practice"
            target_skill = inferred_skill or "vector_components"
            tool_res, summary = self.execute_tool(
                conn,
                session_id,
                tool_name="start_practice",
                args={"skill_id": target_skill}
            )
            tool_result = tool_res
            reply_text = f"I've initiated a fresh 3-question practice session on {target_skill}. Solve them to verify your recovery."

        # 5. Explain Skill Intent (if skill was inferred!)
        elif inferred_skill:
            requested_action = "explain_skill"
            target_skill = inferred_skill
            tool_res, summary = self.execute_tool(
                conn,
                session_id,
                tool_name="explain_skill",
                args={"skill_id": target_skill}
            )
            tool_result = tool_res
            note = tool_res.get("note", {})
            reply_text = (
                f"### {note.get('title', 'Skill Review')}\n\n"
                f"{note.get('summary', '')}\n\n"
                f"**Key Formulas:**\n" + "\n".join(f"- {f}" for f in note.get("key_formulas", [])) + "\n\n"
                f"**Common Pitfalls:**\n" + "\n".join(f"- {p}" for p in note.get("common_pitfalls", []))
            )

        # 6. Default Progress Intent (fallback when no skill inferred)
        else:
            requested_action = "get_progress"
            tool_res, summary = self.execute_tool(conn, session_id, tool_name="get_progress", args={})
            tool_result = tool_res
            reply_text = (
                "Here is your current status: Diagnostic evidence and your daily study plan are synchronized. "
                "You can ask me to adjust your study time, explain any micro-skill, or launch fresh practice."
            )

        # Mode determination
        if mode_prefix == "Gemini":
            llm_mode = f"Gemini ({os.environ.get('GEMINI_MODEL', self.gemini_model)})"
        elif mode_prefix and "Agent Router" in mode_prefix:
            llm_mode = mode_prefix
        elif self.agent_router_key:
            llm_mode = f"Deterministic Engine (Agent Router Fallback: {self.agent_router_model})"
        else:
            llm_mode = "Deterministic Engine (Rule Routing & Verification)"

        # Save run in DB
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO agent_runs (
            id, session_id, status, requested_action, user_message, tool_result_json, reply_text, llm_mode, created_at
        ) VALUES (?, ?, 'completed', ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            session_id,
            requested_action,
            message,
            json.dumps(tool_result) if tool_result else None,
            reply_text,
            llm_mode,
            now_iso
        ))

        return AgentRunOut(
            run_id=run_id,
            session_id=session_id,
            status="completed",
            requested_action=requested_action,
            tool_result=tool_result,
            reply_text=reply_text,
            llm_mode=llm_mode,
            error_code=None,
            created_at=now_iso
        )


mentor_service = MentorService()
