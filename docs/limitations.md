# PathPilot: Known Limitations & Scope Boundaries

This document provides a transparent accounting of the current boundaries, limitations, and future roadmap for PathPilot as of the November 2026 competition submission.

---

## 1. Pedagogical & Diagnostic Limitations

1. **Micro-Skill Topic Pack vs. Full Syllabus:**
   - *Current Implementation:* Supports exactly three micro-skills in JEE Physics (`vector_components`, `vector_addition`, `constant_accel_1d`).
   - *Limitation:* Does not cover rotational mechanics, electromagnetism, modern physics, or mathematics/chemistry.
   - *Future Work:* Systematic expansion into topic packs with dependency DAG validation.

2. **Fixed Diagnostic vs. Adaptive IRT:**
   - *Current Implementation:* Delivers a fixed 9-question diagnostic (3 items per micro-skill).
   - *Limitation:* The diagnostic is fixed, not an adaptive Item Response Theory (IRT) or knowledge-tracing engine. It is not advertised as adaptive.
   - *Honest Labeling:* The application presents scores with an explicit sample caveat: *"Small sample (3 questions). Demonstrates immediate diagnostic pattern, not durable exam mastery."*

3. **Separation of Retest Evidence:**
   - *Current Implementation:* Diagnostic counts and subsequent practice scores are maintained and displayed in separate fields.
   - *Limitation:* A 3-item retest provides limited evidence of short-term recall and formula application; it does not prove long-term retention or exam score improvement.

4. **Task Completion Guardrail:**
   - Marking study tasks completed updates schedule progress, but does **not** increment assessment scores without taking a fresh graded quiz.

---

## 2. Planning & Scheduling Limitations

1. **Single-Day Recovery vs. Multi-Week Timeline:**
   - *Current Implementation:* Computes today's schedule fitted strictly within remaining daily minutes ($15$ to $240$ min).
   - *Limitation:* Does not build a multi-month calendar, handle rest days across time zones, or project exam-day milestone deadlines.
   - *Future Work:* Spaced repetition review queues and multi-day planning algorithms.

2. **Explicit Task Deferral:**
   - When a student's daily time budget is reduced (e.g. from 45 min to 30 min), tasks that cannot fit are explicitly recorded in `deferred_tasks` rather than dropped silently.

---

## 3. Autonomous Agent & LLM Limitations

1. **Constrained Tool Allowlists:**
   - The mentor agent can only execute five allowlisted backend functions (`get_progress`, `explain_skill`, `start_practice`, `replan`, `compare_rank`).
   - The model cannot query raw SQL, execute code, modify marks, or access data outside the authenticated session.

2. **Truthful Fallback Mode:**
   - When no external LLM API key is provided, or if the model provider times out, PathPilot seamlessly routes commands via its deterministic intent router.
   - The UI truthfully reports: `Mode: Deterministic Engine (Rule Routing & Verification)`. It does not disguise scripted replies as a live neural agent.

---

## 4. College Admissions & Historical Comparison Limitations

1. **Historical Comparison vs. Admission Probability:**
   - *Current Implementation:* Compares an entered JEE Main CRL rank against published JoSAA 2024 Round 5 closing ranks for NIT CS (Open, Other State).
   - *Limitation:* This is an empirical historical comparison. It is **not** an admission probability, predictive forecast, or eligibility certification.
   - *Guardrail:* The API strictly rejects category rank lists (OBC-NCL, SC, ST) or JEE Advanced ranks against this CRL cohort to prevent invalid comparisons.

