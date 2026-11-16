# PathPilot: build-ready submission and full-scale agent plan

Revised: 15 November 2026. Team: 2 people. Submission deadline: today, 9:00 PM IST, supplied by you. Planning started at approximately 4:05 PM IST; if you begin later, shorten development and preserve the submission buffer.

This replaces the supplied PathPilot plan. It is a specification, not a claim that the software, datasets, tests, or deployment already exist. The original file in Downloads remains unchanged. See `PathPilot_Issue_Audit.md` for the corrections.

**Decision: build a small, persistent student recovery agent tonight. Expand it into an evidence-based learning platform after submission.** Keep the existing React/Python direction where practical. Do not spend tonight assembling Redis, vector search, several model chains, or a multi-agent system.

## 1. Verified competition requirements

I read all six pages of the [official problem statement and judging guide](https://drive.google.com/file/d/1JLT1iZ0Z-Ao43uQ5COwQyQEgkTs3Re2H/view?usp=sharing), including Track 4 on page 4 and submissions/judging on pages 5–6. The email links to this guide; it does not itself provide the detailed rules.

| Official requirement | What it means for this project |
|---|---|
| Pick one of five broad tracks; working solutions to problems within a track are allowed | Select Track 4: Smart AI Helpers for Coding, Work & Student Learning |
| Track 4 allows an action-taking agent OR a student learning/career simulator | PathPilot can use the education option; cross-app coding automation is not required |
| Student example: quick assessment/profile, identify weaknesses, simulate exam/college prospects, generate a daily plan | Demonstrate diagnosis, an honest scenario tool, and a usable plan |
| Mandatory 8–10-slide PPT or PDF | Prepare a 9-slide deck |
| Mandatory actual GitHub/GitLab code link | Repository must contain runnable source and setup instructions |
| Optional 2–3-minute working demo video | Up to 15 extra points; show the application working |
| Scoring | Usefulness 25; working technology 25; simplicity 20; speed/safety/readiness 15; clear/honest presentation 15 |

Source: official guide, pages 1, 4–6. A database and working logic support the technology criterion; more infrastructure is not itself a scoring advantage.

**Not specified in the guide:** a required language/framework, JEE specifically, Redis, LangGraph, multilingual support, Monte Carlo, number of questions, or a 10-day build period. Your deadline and two-person team are user constraints. Eligibility, upload size limits, exact submission form fields, and any later organizer updates still need checking on the event portal. Do not assume a hosted URL is separately mandatory; the deck should contain working project/demo links, and hosting is strongly useful if feasible.

## 2. Focused product

**Pitch:** PathPilot helps a student discover a specific learning gap, complete a short recovery activity, and adjust today's study plan when time or performance changes.

Target for tonight: a student practicing a small JEE-oriented physics sample. Support exactly three micro-skills:

1. Vector components.
2. Vector addition.
3. Constant-acceleration motion in one dimension.

Treat this as a sample topic pack, not complete JEE coverage. Author and review 18 original MCQs: three diagnostic and three fresh practice questions per skill. Label questions by purpose so the same item cannot establish improvement after its solution has been shown. If a reliable bank already exists, reuse it after checking provenance and answers.

The user journey is:

```text
Start demo → choose daily minutes → answer 9 questions
  → see performance by skill, with sample counts
  → build today's plan → ask for help / request a smaller plan
  → complete fresh practice → save results → update the plan
```

Keep a separate historical college comparison panel. The student supplies a rank scenario; the application compares it with a small set of verified historical cutoffs. Do not derive a rank from nine questions.

**The real-world problem solved in the demo:** “I got vector questions wrong, missed yesterday, and only have 30 minutes today.” The app selects the relevant explanation and fresh practice, reduces the schedule to fit 30 minutes, saves the new version, and shows what changed.

## 3. Tonight's feature boundary

| Must work by feature freeze | Acceptance evidence |
|---|---|
| Anonymous demo session | Separate browser sessions cannot access each other's data |
| Nine-question diagnostic | Server grades it and saves each answer immediately |
| Weakness summary | Three skill cards show correct/attempted and limited evidence |
| Deterministic daily planner | Task minutes fit the student's actual budget |
| Mentor with constrained tools | At least one natural-language request triggers a real backend action |
| Practice feedback | Fresh questions, reviewed answers, persisted result |
| Replanning | Request changes the saved plan; completed tasks remain recorded |
| Scenario panel | Verified cutoff rows and rank comparison, or explicitly labeled synthetic demonstration |
| Submission package | Runnable code, README, 9-slide deck, working demo evidence |

Do not build tonight: production registration, password recovery, live question generation, voice, WhatsApp/email reminders, leaderboards, full syllabus, calibrated admission probabilities, automatic external browsing, vector database, Redis queue, offline answer synchronization, or parallel agents.

English is the default. Add Hindi only if one person can review the entire demonstrated flow before feature freeze. A partially translated UI is not a required compromise.

## 4. Two-person schedule until 9:00 PM IST

The exact clock below is a suggested execution schedule, not an event rule. Adjust the first block if this document is opened later. Reserve the final 20 minutes for submission.

| Time today | Person A: backend and data | Person B: UI and submission | Exit gate |
|---|---|---|---|
| 4:15–4:30 | Agree response schemas; initialize DB and API | Create screens; open event portal; start deck outline | Both use the same three skill IDs and API fields |
| 4:30–5:15 | Seed/review 18 questions; implement sessions, grading and persistence | Build diagnostic and results screens using shared fixtures | A real answer round trip works |
| 5:15–6:00 | Planner, task status, replan transaction | Connect results, Today view, task controls | Diagnostic → saved plan works after reload |
| 6:00–6:35 | Mentor tool routing; reviewed explanations; practice endpoint | Mentor panel and before/after plan view | “Only 30 minutes today” changes the persisted plan |
| 6:35–7:00 | Cutoff comparison and source validation | Scenario panel and responsive/error pass | Complete thin slice; no new features after 7:00 |
| 7:00–7:30 | Run critical checks; fix integration bugs; deployment attempt | Finish 9-slide deck with actual screenshots | App, README and deck reflect reality |
| 7:30–8:00 | Clean-start check and code-link permissions | Record 2–3-minute video; export/check deck | All required artifacts exist |
| 8:00–8:40 | Fix only blockers; verify repo/setup | Verify every link and portal field; stage submission | Submission ready before final buffer |
| 8:40–9:00 | Support submission | Upload/submit; retain confirmation | Actual submission confirmation received |

Both people should independently solve the question bank before using it. Budget roughly 20 minutes each for simple items, and reduce complexity rather than shipping ambiguous questions.

**Fallback gates:**

- If behind at 5:15: use a single page with tabs; cut charts and custom styling.
- If behind at 6:00: keep a fixed diagnostic. Adaptive selection is a later feature.
- If the model integration is not reliable by 6:35: keep tool buttons and reviewed explanations working, label the AI interaction incomplete, and describe this honestly in the deck. Do not disguise scripted replies as a functioning AI agent.
- If cutoff data cannot be verified within 20 minutes: use three clearly marked synthetic rows to demonstrate the comparison algorithm. Show “illustrative data; not college advice” and list real-data integration as unfinished. This reduces completeness, but is better than fabricated real college numbers.
- If hosting is not working by 7:30: stop infrastructure work, record the local working app, and provide exact setup instructions and the code link. Verify the portal accepts the available demo format.
- At 8:00: stop adding features. The mandatory deck and code link take priority over optional polish.

## 5. Architecture for tonight

Use React + Vite + TypeScript for the UI, FastAPI + Pydantic for the API, and SQLite for a single-process demonstration if no working PostgreSQL setup already exists. Keep PostgreSQL if it is already configured. SQLite is an explicit time-saving choice; a local file on ephemeral hosting is not durable production storage.

```text
React UI
  └─ /api/v1 over same origin
       └─ FastAPI
            ├─ grading / skill evidence / planner / cutoff comparison
            ├─ mentor router → allowlisted service functions
            ├─ reviewed questions and notes
            └─ SQLite file OR existing PostgreSQL
```

In development, proxy `/api` from Vite to FastAPI. For a simple deployment, build the frontend and serve its static assets from FastAPI; register API routes before the SPA fallback. This avoids two deployments and cross-origin cookie complexity. One writable persistent volume is required if a hosted demonstration uses SQLite. Run one application process for that configuration.

Use the model provider for which you already have working access. Configure its model identifier through an environment variable and verify a small tool-call request immediately. No particular model/provider is required by the competition. Keep provider keys only on the backend.

Tonight, a small explicit state machine is enough. Retain LangGraph for the longer-term design from the supplied plan, but installing and learning it is not a deadline requirement.

### Suggested repository layout

```text
pathpilot/
  README.md
  .env.example
  .gitignore
  DATA_SOURCES.md
  backend/
    app/main.py
    app/db.py
    app/schemas.py
    app/routes.py
    app/services/{grading,planner,mentor,scenarios}.py
    data/{skills,questions,notes,cutoffs}.json
    tests/test_core.py
    requirements.txt
  frontend/
    src/{App,api}.tsx
    src/components/
    package.json
    package-lock.json
  docs/
    demo-script.md
    limitations.md
```

The README must include installed runtime versions, environment variables, seed/start/build commands, example usage, verified features, limitations, and source provenance. Pin the environment that actually passed the clean-start check. Do not copy untested version combinations from the old plan.

The original Tailwind command mixes current installation with the old `init -p` workflow. Either use plain CSS tonight or follow the [current Tailwind Vite setup](https://tailwindcss.com/docs/installation/using-vite): `tailwindcss` plus `@tailwindcss/vite`, configure the Vite plugin, and import Tailwind in CSS. Preserve the React Vite plugin too.

## 6. The smallest genuine agent

An agent must complete a task and verify its effect. Streaming chat alone does not prove this.

```text
Receive request
 → load this session's profile, skill evidence and active plan
 → classify intent and validate structured arguments
 → call one allowed tool
 → verify tool result / database state
 → return explanation plus a visible result card
```

| Tool | Validated inputs | Effect / output |
|---|---|---|
| `get_progress()` | None; session identity supplied by server | Skill evidence and current plan |
| `explain_skill(skill_id)` | One supported skill | Reviewed note and optional model explanation |
| `start_practice(skill_id)` | Supported skill with unused items | Creates a practice session, returns public question fields |
| `replan(available_minutes, reason, expected_version)` | Positive bounded minutes; current version | Saves a revised plan and returns its diff |
| `compare_rank(rank, cohort_key)` | Positive integer, supported cohort | Historical scenario comparison, source and year |

The model cannot set a user ID, query arbitrary SQL, execute code, change marks, fabricate dataset records, send messages, or submit admissions forms. Read the session ID from the authenticated server context, never from model arguments.

**Authorization behavior:** a direct request such as “Make today's plan 30 minutes” authorizes that reversible change. Execute it and show the outcome. “What if I only had 30 minutes?” requests a preview; save nothing until the student chooses to apply it. Preserve previous versions so Undo creates a new version with restored pending tasks.

**Limits proposed for tonight:** maximum three tool calls, two model calls, and 20 seconds per run. On timeout, retain any completed tool result and show its actual status. Do not rerun a write merely because the final narration failed. If ambiguous, offer a choice of supported actions. The UI shows actions and results, not private model reasoning.

Example result, clearly illustrative:

```json
{
  "status": "completed",
  "action": "replan",
  "previous_version": 2,
  "plan_version": 3,
  "available_minutes": 30,
  "scheduled_minutes": 30,
  "tasks": [
    {"kind": "learn", "skill_id": "vector_components", "minutes": 10},
    {"kind": "practice", "skill_id": "vector_components", "minutes": 15},
    {"kind": "review", "skill_id": "vector_addition", "minutes": 5}
  ],
  "deferred_task_ids": ["pending-motion-task"],
  "warnings": ["Performance evidence is based on a small sample."]
}
```

## 7. Corrected diagnostic and learning logic

### Tonight: evidence counts rather than false precision

- Fixed nine-item diagnostic, three per skill; do not call it adaptive.
- Grade exclusively on the backend. Never include correct answers in the question payload before submission.
- Show “1 of 3 correct; needs practice” with “small sample” beside it. Show “not assessed” for other skills.
- Mark errors using reviewed distractor tags when available: component/sign confusion, vector addition confusion, equation selection. A distractor suggests a possible misconception; it does not prove its cause.
- Display “possible prerequisite gap” only when the prerequisite has actually been assessed. Never infer a causal root problem from two low scores alone.
- Completing a lesson updates task status, not skill competence. Only a fresh assessment changes performance evidence.
- Keep diagnostic and subsequent practice results separately visible. A three-item retest demonstrates the feedback loop; it cannot establish durable learning or real exam improvement.

### Later: adaptive, uncertainty-aware assessment

Track evidence by micro-skill, difficulty and question version. Use an initial coverage pass, then select unused items where evidence is limited. Bound assessment length and allow “not enough evidence” when the bank is exhausted.

A transparent baseline for comparable, unaided items is Beta-Binomial tracking: `alpha = 1 + correct`, `beta = 1 + incorrect`. The posterior is a model of success on comparable items under simplifying assumptions, not an established measure of student mastery. Guessing, different difficulty, adaptive selection and repeated exposure violate those assumptions unless explicitly modeled. Keep skips, hints and repeated items separate; do not count translation variants as new evidence.

Validate any thresholds on held-out items. Later, evaluate calibrated item-response or knowledge-tracing models against the simple baseline before replacing it. Estimated confidence should reflect item quality and coverage, not only `1/sqrt(n)`.

## 8. Corrected planning algorithm

Inputs: current skill evidence, today's remaining minutes, selected goal, completed tasks and available reviewed content. The exam date may be stored, but tonight's schedule covers today only.

1. Preserve completed tasks and past records.
2. Select the weakest assessed skill; tie-break deterministically by configured learning order. Do not equate missing evidence with weakness.
3. Schedule a short explanation, fresh practice and review. If a prerequisite is both supported and weak, schedule it first.
4. Fit task durations within the remaining budget. For 30 minutes, use 10 + 15 + 5. For less than a complete practice block, offer one short review and defer the rest.
5. Record deferred work explicitly. Never silently claim that all goals fit.
6. Save a new version atomically and return what changed and why.

For a multi-day planner later, add per-day availability, rest days, time zones, prerequisite DAG validation, spaced reviews and exam-date boundaries. Allocate by expected utility per minute using validated or explicitly assumed weights, not simply `priority × est_hours`, which favors large chapters. A full mock must fit a real available block. On an impossible deadline, show the shortfall and offer a narrower goal.

Replan after a meaningful new result or an explicit time change; debounce repeated events. Do not rebuild the entire schedule after every click. A study-hours slider changes available work, not the student's demonstrated competence.

## 9. Honest simulation and college comparisons

The original normal-distribution simulation, arbitrary study boost and raw-score-to-rank interpolation do not justify admission percentages. The replacement has three distinct layers:

**Tonight: historical rank scenario.** Enter an actual or hypothetical rank and compare it with compatible published closing ranks. Show “at or better than this historical closing rank” or “outside this historical closing rank.” This is a historical comparison, not admission probability, eligibility certification or a future guarantee.

Source records from [JoSAA's official opening/closing rank portal](https://josaa.nic.in/or-cr/). Preserve institution, program, year, round, quota, seat category, gender pool, rank-list type, opening/closing ranks, source URL and retrieval date. JoSAA explicitly distinguishes open-seat CRL from category and PwD ranks: [official rank definitions](https://josaa.admissions.nic.in/Applicant/seatallotmentresult/currentorcr.aspx). Never compare different rank types or mix IIT/JEE Advanced and JEE Main admission routes.

For tonight, support one clearly identified compatible NIT+ cohort and three verified program rows. The user must select that cohort explicitly. If their situation does not match, return “unsupported scenario.” No government IDs, certificates or sensitive profile uploads are needed for a demo.

**Later: interval scenarios.** If the user supplies a plausible rank interval `[r_best, r_worst]`, with smaller ranks better and historical closing rank `c`:

```text
r_worst <= c  → entire scenario interval meets the historical rank threshold
r_best > c    → entire scenario interval misses it
otherwise    → interval crosses the threshold
```

Label the interval as user supplied or identify its validated source. Missing compatible rows mean unavailable, never zero chance. Historical variation can be shown by year without turning the fraction of favorable years into a personal admission probability.

**Research stage: calibrated exam forecasting.** A full exam estimator requires an appropriate test blueprint, question-type/marking configuration, attempts and omissions, calibrated item performance, and validation against real independent mocks. Raw marks, normalized scores and final ranks are different quantities; a universal deterministic mapping is not justified. NTA's [2026 official result notice](https://www.nta.ac.in/Download/Notice/Notice_20260216182125.pdf) describes shift-relative scoring and later final rank preparation. Reverify the applicable exam year's official rules before implementation.

Any future Monte Carlo output is conditional on model assumptions. Match empirical interval coverage on held-out data; evaluate by subgroup and year where sample sizes permit. Do not publish personal admission probabilities until outcome calibration supports them. Without data, show scenario results and assumptions instead.

## 10. Data and API contract for tonight

Suggested minimal tables; use foreign keys and UTC timestamps:

| Table | Essential fields |
|---|---|
| `demo_sessions` | id, hashed opaque token, created_at, expires_at |
| `profiles` | session_id, daily_minutes, language |
| `questions` | id, version, skill_id, purpose, stem, options, answer_key, explanation, reviewed_by |
| `assessments` | id, session_id, kind, status, created_at, completed_at |
| `assessment_items` | id, assessment_id, question_id, ordinal |
| `answers` | assessment_item_id, selected_option, correctness, skipped, created_at |
| `plans` | id, session_id, version, available_minutes, created_at |
| `tasks` | id, plan_id, skill_id, kind, minutes, status, source_task_id |
| `agent_runs` | id, session_id, status, requested_action, tool_result, error_code, created_at |
| `idempotency_keys` | session_id, route, key, request_hash, response_json |
| `cutoffs` | complete cohort fields described above, ranks, source_url, retrieved_at |

Constraints: unique answer per assessment item; unique `(session_id, version)` for plans; positive task minutes; unique idempotency tuple; current plan pointer updated in the same transaction as plan creation. Questions and answer keys are versioned so edits cannot rewrite historical results.

| Endpoint under `/api/v1` | Behavior |
|---|---|
| `POST /demo-sessions` | Create server-owned anonymous session and secure cookie |
| `PUT /profile` | Validate time budget/language |
| `POST /assessments` | Start diagnostic/practice from reviewed bank |
| `POST /assessments/{id}/answers` | Validate ownership and assigned item; grade and commit; return next item |
| `GET /assessments/{id}/results` | Return per-skill counts and sample caveat |
| `GET /progress` | Current profile, evidence and plan version |
| `POST /plans` | Generate/save initial plan |
| `POST /plans/replan` | Apply requested change with expected version |
| `PATCH /tasks/{id}` | Record completion/skip without inventing assessment evidence |
| `POST /mentor/runs` | Execute bounded mentor workflow, return result card |
| `GET /mentor/runs/{id}` | Recover status/result after a lost response |
| `POST /scenarios/rank` | Compare compatible historical cutoff rows |
| `GET /health` | Process health; expose no secrets |

Write endpoints accept `Idempotency-Key`. A retry with the same key and body returns the saved response; the same key with different content returns conflict. Duplicate prevention must live in the database, not in a ten-minute Redis lock. Answer insert, result update and stored idempotent response belong in one transaction.

For replanning, check `expected_version` and create the new plan atomically. Return HTTP 409 for a stale version. Use 401/403 for session/ownership failures, 422 for invalid inputs, 429 for limits and 503 for temporarily unavailable dependencies. Error shape: `{code, message, request_id, retryable}`.

## 11. Real-time behavior and recovery

Tonight, use normal HTTP responses and immediate UI updates. A spinner plus persisted run status is enough; streaming is optional. Never hold a database transaction open across an LLM network call.

Later, separate run creation from streaming:

```text
POST /mentor/runs → {run_id}
GET /mentor/runs/{id}/events → SSE
GET /mentor/runs/{id} → authoritative persisted status/result
```

Event types: `run.started`, `tool.started`, `tool.completed`, `plan.updated`, `message.delta`, `run.completed`, `run.failed`. Include run ID, event sequence, timestamp and schema version. Enforce owner access on both status and stream. Store business events durably; token deltas can be transient if final messages are saved.

Native EventSource is for a URL-based SSE connection; it is not interchangeable with sending a JSON POST body or arbitrary Authorization headers. Use same-origin session cookies for GET streaming, or `fetch` streaming when request headers/body require it. See [MDN EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource).

On reconnect, replay durable events after the last ID; when retention has expired, fetch the current snapshot. Redis pub/sub alone cannot provide replay. Polling is a valid fallback. Disable proxy buffering on stream routes and test timeouts before claiming streaming works.

Proposed targets, to measure rather than claim: persisted answer response under 1 second; deterministic replan under 2 seconds; mentor result under 20 seconds with a timeout fallback. Record the actual environment, number of users and observed timings in the deck.

## 12. Full-scale architecture after submission

```text
Web client
  → API / session and authorization boundary
      → assessment, evidence, planning, scenario services
      → durable mentor state machine
          → typed, allowlisted service tools
          → reviewed-content retrieval
          → model provider adapter
      → PostgreSQL: application truth, run ledger, events, outbox
      → worker: imports, content review preparation, scheduled jobs
      → Redis: optional caches, rate limits, queue transport
```

Retain FastAPI, React and the supplied LangGraph direction when expanding. Use a persistent PostgreSQL checkpointer for agent state. LangGraph distinguishes thread checkpoints from cross-thread stores; in-memory checkpoints do not survive restarts. See [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence).

**Agent state:** run ID, user ID bound by server, goal, input versions, retrieved source IDs, current action, tool-call budget, deadline, result, error and checkpoint version. Every mutating tool has a durable operation ID and idempotent service boundary. Checkpoints do not by themselves prevent duplicate external side effects.

**Durable work:** insert an outbox event with the business transaction; a worker claims it, executes an idempotent handler, and marks completion. Recover expired leases. Add bounded retries with backoff, dead-letter inspection, and administrative replay. PostgreSQL retains job intent/status even if Redis is cleared. Redis queues may assist delivery; they do not replace that record.

**Concurrency:** optimistic versions on plans, bounded per-user active runs, a single event identity for deduplication, and explicit conflict handling. Canceling a run stops future work; already committed tool actions must still be reported accurately.

**Retrieval:** start with reviewed notes indexed by skill; add hybrid keyword/vector search only when the corpus needs it. Every chunk carries document version, source, license, language, skill and location. The [multilingual E5 model card](https://huggingface.co/intfloat/multilingual-e5-small) specifies 384-dimensional embeddings, `query:`/`passage:` prefixes and a 512-token input limit. Chunk using the model tokenizer with room for metadata; tune thresholds using English/Hindi evaluation questions, not a universal similarity constant.

**Content quality:** draft → structural validation → independent solution → human review → approved version. Agreement between two model calls is not proof of correctness. Use constrained arithmetic/unit checks where appropriate; do not execute model-generated code. Quarantine reported items and exclude invalidated answers from recomputed evidence while retaining the audit trail.

**Personalization:** store explicit preferences and validated learning evidence. Keep transient chat separate from durable facts. Bound history, record provenance and allow correction/deletion. Personalized responses must never enter a shared cache keyed only by question ID.

**Scaling path:** instrument first; add database pooling and appropriate indexes, then stateless API replicas and independently scaled workers. Keep streams and model concurrency within measured provider limits. Build vector indexes after measuring retrieval volume. Avoid Kubernetes and additional databases unless observed requirements justify them.

## 13. Privacy, safety, cost and operating model

For tonight, use synthetic demo identities and anonymous sessions. Use unguessable tokens in HttpOnly cookies, Secure in hosted HTTPS, and a restrictive SameSite setting. Scope all objects to the session; validate Origin/CSRF protection for cookie-authenticated mutations. Do not expose a shared mutable student account to all judges. A fresh “Start demo” session should receive its own data.

For production, add a maintained authentication approach, authorization tests, session revocation, consent/age handling appropriate to the intended launch population, retention policies and account deletion. Confirm applicable requirements before admitting real minors; this plan does not certify legal compliance. Keep optional admission cohort data minimal and purpose-limited.

Sanitize rendered Markdown; no raw model-generated HTML. Treat student text, retrieved notes and imported documents as untrusted data. Tool allowlists, ownership checks and argument validation must enforce policy even if a prompt is manipulated. Redact logs and avoid sending identifiable profiles to the model when aggregated skill evidence is enough.

Do not promise admission, rank, intelligence assessments or guaranteed improvement. For serious distress, offer a supportive response and an appropriate human-help path; keep the product's scope educational. No public performance leaderboard is needed.

Operational controls: request IDs, provider timeouts, per-session usage limits, input/output token caps, run counters, structured error logs and a deterministic fallback. Do not say “all hosting is free.” Verify chosen host/storage limits and current prices before purchasing or committing.

Measure cost as:

```text
daily cost = model input tokens × current input rate
           + model output tokens × current output rate
           + embeddings and other metered services
           + daily share of hosting/storage
cost per active student = daily cost / measured active students
```

Report the pricing date, currency, assumptions and whether figures are measured or projected. Do not invent a cost/student number for the PPT.

## 14. Verification and release gates

Tonight's checks are deliberately short and consequential:

1. Complete the full journey from a fresh session, then reload and confirm persistence.
2. Submit one answer twice and verify only one record and one update exist.
3. Attempt to fetch another session's assessment or plan; access must fail.
4. Ask for a 30-minute plan; verify the sum, saved version and visible change.
5. Complete a task; verify that correctness counts do not increase without a quiz.
6. Submit a fresh practice answer; verify the right skill updates and earlier records remain.
7. Disable/fail the LLM call; diagnostic/planning still work and the UI describes the failure truthfully.
8. Use an incompatible rank type or missing source row; return unsupported/unavailable.
9. Check the phone-width layout and keyboard navigation on the critical flow.
10. Start from the README on the other teammate's machine; verify code, deck and video links in a signed-out browser where possible.

Full-scale gates add crash recovery, Redis-loss recovery, event replay, concurrent replans, deletion coverage across checkpoints/caches/backups, prompt-injection probes, content review, empirical calibration and load tests on stated hardware. Use measured task success and fresh-item learning evidence; model agreement and schema validity alone are insufficient quality metrics.

A small usability test can establish whether people find the next action. It cannot establish that PathPilot improves exam outcomes. Any before/after result in the deck must identify whether it is a synthetic demonstration or real observed data.

## 15. Submission package

### Nine-slide deck

1. PathPilot, team, Track 4 and one-sentence student problem.
2. Target user and the precise learning/time-management problem; avoid uncited market statistics.
3. Working journey: diagnostic → evidence → plan → practice → replan.
4. Actual screenshots of the diagnostic and skill results.
5. Agent action: a natural-language time change produces a saved plan diff.
6. Architecture and what deterministic code versus the model does.
7. Historical scenario comparison, data provenance and its limitations.
8. Actual checks, timings, usability observations and incomplete features.
9. Code link, demo/video link, setup instructions and the next milestone.

### 2–3-minute video, optional bonus

| Time | What to show |
|---|---|
| 0:00–0:15 | State the problem and demonstrate the Start button |
| 0:15–0:40 | Answer a few diagnostic questions; label any pre-seeded or shortened demo |
| 0:40–1:00 | Skill evidence and a generated plan |
| 1:00–1:35 | Ask “I only have 30 minutes”; show tool result and persisted plan change |
| 1:35–2:00 | Fresh practice, reviewed explanation and saved result |
| 2:00–2:20 | Historical rank comparison with source, year and no guarantee wording |
| 2:20–2:40 | Reload to prove persistence; show limitations and project links |

Never display a live API key, personal student record or email account. If a feature is a fixture, name it. Do not claim simulated timings or screenshots are live results.

### Final checklist

- [ ] Code repository opens for judges and contains source, seed data and instructions.
- [ ] No credentials, private database files, personal data or unnecessary model traces committed.
- [ ] Deck has 8–10 slides and opens correctly after export.
- [ ] Every link works with the intended access permissions.
- [ ] Video is 2–3 minutes if included and shows the actual app.
- [ ] User-supplied 9:00 PM IST deadline is respected; actual portal instructions checked.
- [ ] Submission completed and confirmation retained before 9:00 PM.

## 16. Roadmap after tonight

These are planning estimates for two people, not promises; measure progress at each gate.

| Phase | Scope | Gate before continuing |
|---|---|---|
| Next 2–3 days | Fix demo defects, PostgreSQL migration if needed, ownership tests, persistent hosting | Reproducible end-to-end flow without data loss |
| Week 1–2 | Expand one topic pack, reviewed bilingual content, prerequisite model, adaptive assessment | Fresh-item evaluation and reliable content review |
| Week 3–4 | Durable LangGraph runs, outbox worker, event replay, multi-day plans | Restart/retry/concurrency tests pass |
| Week 5–6 | Carefully consented pilot, calibrated evidence thresholds, usability and cost measurement | Explicit quality targets met on held-out examples |
| Week 7–8+ | Broader topic coverage, verified cutoff ingestion, optional reminders, measured capacity work | Privacy, data-quality and reliability gates passed |
| Research-dependent | Full-exam forecasting and personal outcome probabilities | Adequate representative longitudinal data and demonstrated calibration |

Do not add a second exam simply because two weeks have passed. Reuse the architecture only after the first topic pack and evidence loop are reliable. Full-scale readiness means reliable data, bounded actions, recovery, evaluation and clear user outcomes; it is not a count of agents or services.
