# PathPilot: Competition Presentation Deck (9 Slides)

**Track:** Track 4 – Smart AI Helpers for Coding, Work & Student Learning  
**Event:** Competition Submission (15 November 2026)  
**Deliverable:** 9-Slide Presentation Structure  

---

## Slide 1: Title & Problem Overview
- **Title:** PathPilot: Autonomous Student Recovery & Dynamic Study Re-Planner
- **Subtitle:** Closing JEE Physics Micro-Gaps Through Action-Taking AI Mentorship
- **Track:** Track 4 (Smart AI Helpers for Student Learning)
- **One-Sentence Problem:**  
  *When competitive exam students encounter conceptual gaps and daily schedule disruptions, static syllabi fail to adapt—leading to abandoned study plans and unaddressed misconceptions.*

---

## Slide 2: Target Student & The Specific Friction Point
- **Target User:** JEE Main physics aspirants practicing foundational mechanics under daily time constraints.
- **The Core Friction Point:**
  - Standard study planners assume infinite time and uniform progress.
  - When a student struggles with a prerequisite (e.g., resolving vector components in Quadrant 2) and misses a 60-minute session, existing apps either pile on overdue tasks or reset arbitrarily.
  - The student needs:
    1. Precise identification of the micro-skill gap (not generic "study more physics").
    2. An honest daily plan that strictly fits remaining minutes (e.g. "I only have 30 minutes today").
    3. Reversible, action-taking recovery without fabricated mastery scores.

---

## Slide 3: The End-to-End Recovery Journey
```text
[1. Start Demo] ──> [2. 9-Item Diagnostic] ──> [3. Evidence & Misconceptions]
                             │                                │
                             ▼                                ▼
[6. Practice Retest] <── [5. AI Mentor Action] <── [4. Deterministic Plan]
                             │
                             ▼
                 [7. Historical Cutoffs]
```
1. **Diagnostic:** 9 calibrated questions (3 per skill) graded strictly on backend.
2. **Evidence Profile:** Explicit correctness ratios, distractor tags, and sample-size caveats.
3. **Daily Planner:** Deterministic time-budget scheduler prioritizing prerequisite recovery.
4. **Autonomous Mentor:** Natural language intent routing executing allowlisted database tools.
5. **Fresh Practice:** Retest using distinct items to verify recovery without memorization bias.
6. **Scenario Explorer:** JoSAA 2024 historical closing rank comparison with strict rank-type validation.

---

## Slide 4: Diagnostic Grader & Skill Evidence Cards
- **Pedagogical Design:**
  - 3 Focused Micro-Skills: `vector_components`, `vector_addition`, `constant_accel_1d`.
  - Server-Enforced Grading: Question options sent without answer keys; grading occurs inside atomic DB transactions.
  - Cognitive Distractor Tagging: Wrong choices identify specific errors (`component/sign confusion`, `cos/sin inversion`, `velocity-distance confusion`).
- **Honest Evidence Presentation:**
  - Shows exact counts: e.g., *"1 of 3 correct; needs practice"*.
  - Explicit Disclaimer: *"Small sample (3 questions). Demonstrates immediate diagnostic pattern, not durable exam mastery."*
  - Subsequent practice counts are tracked in a separate column to prevent confusing initial baseline with fresh practice.

---

## Slide 5: Genuine Agent Action – The 30-Minute Re-Plan
- **Prompt:** *"I only have 30 minutes today."*
- **Action Execution:**
  - The Mentor classifies the intent as a time-budget replan.
  - Calls allowlisted service tool: `replan(available_minutes=30, expected_version=1)`.
  - Atomically creates **Plan Version 2** in SQLite WAL database.
- **Outcome & Visible Diff:**
  - Scheduled minutes fit budget: $10\text{ min learn} + 15\text{ min practice} + 5\text{ min review} = 30\text{ min}$.
  - Non-fitting items explicitly moved to `deferred_tasks` with reasons, preventing schedule collapse.
  - Generates verifiable Action Card in chat interface detailing DB version bump and minute diff.

---

## Slide 6: Architecture & Boundary of Responsibilities
```text
┌────────────────────────────────────────────────────────┐
│             React + TypeScript + Vite UI               │
│  (Session Cookie + Bearer Token, Optimistic Concurrency)│
└───────────────────────────┬────────────────────────────┘
                            │ /api/v1
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI Backend                     │
│  ├─ Auth Boundary: Isolated Demo Sessions               │
│  ├─ Idempotency Ledger: Duplicate Answer Rejection     │
│  ├─ Deterministic Services: Grading & Time Planner     │
│  └─ Constrained Mentor: Allowlisted Tool Executions    │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
┌─────────────▼────────────┐ ┌─────────────▼─────────────┐
│  SQLite WAL Application  │ │   LLM Provider Adapter    │
│  Truth & Plan Ledger     │ │ (Rules + optional Gemini)   │
└──────────────────────────┘ └───────────────────────────┘
```
- **Deterministic Code:** Grades questions, computes scores, fits minutes into budget, enforces idempotency, validates optimistic concurrency versions.
- **Model Adapter:** Understands conversational phrasing, routes to verified tool definitions, and falls back gracefully to a deterministic router if offline.

---

## Slide 7: JoSAA Historical Scenario & Data Provenance
- **Data Source:** [JoSAA 2024 Round 5 opening and closing rank table (PDF mirror)](https://static.collegedekho.com/media/django-summernote/2024-07-18/6829e64b-86f2-415e-93e2-9661bed006ac.pdf).
- **Compatible Benchmark Cohort:**
  - Three NIT Tiruchirappalli B.Tech programmes, OPEN category, Gender-Neutral, Other State (OS) quota, JEE Main CRL.
  - *NIT Trichy CSE:* Closing Rank 1,224.
  - *NIT Trichy ECE:* Closing Rank 3,546.
  - *NIT Trichy EEE:* Closing Rank 6,040.
- **Strict Guardrails:**
  - Incompatible rank types (e.g. Category ranks or JEE Advanced) rejected with HTTP 422.
  - Prominently labeled: *"Historical comparison only. Does not constitute an admission probability or future guarantee."*

---

## Slide 8: Verification Results & Limitations
- **Verification Gates (Section 14):**
  - **Nine automated acceptance checks** in the runner (`python -m backend.tests.run_acceptance_checks`).
  - Session Isolation: Verified that Session B cannot view or answer Session A's quiz.
  - Idempotency: Duplicate answers with the same key return cached response with exactly 1 DB record.
  - Score Integrity: Marking a task complete does *not* inflate assessment scores.
- **Browser:** Keyboard answer, quiz resume after reload, saved 30-minute replan, completed practice and cutoff comparison at 390 px.
- **Backend:** 14 tests passed. No latency benchmark was run during review.
- **Known Limitations:**
  - 3 micro-skills only (JEE mechanics sample).
  - Single-day recovery (multi-day calendar is future work).
  - Anonymous demo sessions without persistent user accounts.

---

## Slide 9: Deliverables, Setup & Post-Submission Roadmap
- **Delivered Repository Artifacts:**
  - Working Source Code (FastAPI + React TypeScript + SQLite).
  - Complete test suite (`pytest` + `run_acceptance_checks.py`).
  - `README.md`, `.env.example`, `DATA_SOURCES.md`, `REVIEW_REPORT.md`, `demo-script.md`.
- **Run after setup:**
  ```bash
  python run.py
  # Serves both API and React frontend on http://127.0.0.1:8000
  ```
- **Before submitting:** Add the actual code repository and demo links; export and check the 9-page PDF or prepare the PPT.
- **Next Milestones (Weeks 1–4):**
  - Week 1–2: Expand to 5 topic packs; introduce prerequisite DAG validation.
  - Week 3–4: Durable LangGraph checkpointing on PostgreSQL; multi-day recovery calendar.

