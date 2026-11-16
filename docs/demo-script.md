# PathPilot: Working Demo Script (2–3 Minutes)

This step-by-step walkthrough is designed for video recording and live competition presentations. It exercises the full end-to-end recovery journey and validates genuine backend tool actions.

---

## Timing Breakdown

### 0:00 – 0:15: Introduction & Demo Session Setup
- **Screen:** Open `http://localhost:8000` (or `http://localhost:5173`).
- **Narrative:**
  > "Hello, this is PathPilot, built for Track 4: Smart AI Helpers for Student Learning. When students practice JEE Physics, they often miss a foundational micro-skill, fall behind on time, and have no dynamic way to recover. PathPilot shows which skills need practice based on a small sample, generates a realistic daily plan, and autonomously reschedules when available time changes."
- **Action:** Click **"Reset Session"** (or observe fresh session initialized in the header). Notice the Daily Budget selector is set to 45 mins and Engine reports active status.

---

### 0:15 – 0:45: 9-Item Diagnostic & Immediate Graded Feedback
- **Screen:** Tab 1: **"1. Diagnostic & Evidence"**.
- **Action:**
  1. Solve Question 1 (Vector Components): Select option **B** (5√3 N, 5 N). Click **"Next Question"**.
  2. Solve Question 2: Intentionally pick option **A** or **B** to demonstrate misconception detection.
     - *Point out:* The feedback panel immediately displays:
       `Incorrect — Misconception: component/sign confusion`.
       `Explanation: Angle is measured from the positive y-axis...`
  3. Complete remaining 7 questions using keyboard shortcuts (<kbd>A</kbd>-<kbd>D</kbd> or <kbd>1</kbd>-<kbd>4</kbd>, then <kbd>Enter</kbd>).
- **Narrative:**
  > "All grading is executed exclusively on the server—answer keys are never transmitted to the client. When an error is made, PathPilot identifies the underlying misconception using reviewed distractor tags."

---

### 0:45 – 1:05: Skill Evidence Profile & Today's Study Plan
- **Screen:** Review the **Micro-Skill Diagnostic Evidence** cards below the diagnostic, then switch to Tab 2: **"2. Today's Study Plan"**.
- **Narrative:**
  > "Notice how PathPilot presents evidence: each card displays exact attempt ratios, identified misconception tags, and an honest caveat stating this is a 3-item diagnostic sample. In the Today's Plan tab, PathPilot deterministically builds a schedule allocating 45 minutes to concept review and practice on the weakest assessed skill."
- **Action:** Toggle one of the task completion checkboxes.
  - *Point out:* The task marks completed on today's schedule, but the evidence score does *not* artificially increase.

---

### 1:05 – 1:40: Autonomous AI Mentor & 30-Minute Replanning
- **Screen:** Switch to Tab 3: **"3. AI Recovery Mentor"**.
- **Action:**
  1. Click the suggested prompt: **"I only have 30 minutes today"** (or type it in the chat box and press Send).
  2. The mentor analyzes the intent, executes allowlisted tool `replan(available_minutes=30)`, and returns a structured Action Card.
- **Narrative:**
  > "Now the real-world scenario: 'I only have 30 minutes today'. The student tells the mentor in natural language. Instead of a generic conversational reply, the agent triggers a genuine backend database transaction: it atomically updates the study plan to Version 2, schedules 30 minutes for the highest-priority weak skill, and moves remaining tasks into the Deferred Tasks ledger so nothing is silently lost."
- **Action:** Click Tab 2: **"Today's Study Plan"** to show that the schedule is updated to 30 mins, with deferred tasks clearly displayed.

---

### 1:40 – 2:05: Fresh Retest Practice & Separate Evidence
- **Screen:** Switch to Tab 4: **"4. Fresh Retest Practice"**.
- **Action:**
  1. Select **"Vector Components & Decomposition"**.
  2. Answer the 3 fresh practice questions.
  3. Return to Tab 1: **"Diagnostic & Evidence"**.
- **Narrative:**
  > "To verify learning without testing on memorized questions, the student takes 3 fresh practice questions. As seen on the skill card, the subsequent practice metrics update to 3/3, while earlier diagnostic baselines remain distinctly preserved."

---

### 2:05 – 2:25: JoSAA 2024 Historical College Cutoff Comparison
- **Screen:** Switch to Tab 5: **"5. JoSAA Historical Cutoffs"**.
- **Action:**
  1. Enter Rank **1500** under JEE Main CRL. Click **"Compare Rank"**.
     - Shows NIT Trichy (CSE Closing Rank: 1224) -> Outside cutoff.
     - NIT Trichy ECE (Closing Rank: 3546) -> At or better than cutoff.
  2. Change Rank Type to **"OBC-NCL"** and click **"Compare Rank"**.
     - Server rejects with clear validation: *"Incompatible rank type: Selected cohort requires JEE Main CRL."*
- **Narrative:**
  > "Finally, our historical scenario tool compares user ranks against official JoSAA 2024 Round 5 closing ranks for three NIT Tiruchirappalli programmes. Notice our strict guardrails: invalid rank types are rejected, and the comparison is explicitly labeled as historical reference, avoiding misleading admission guarantees."

---

### 2:25 – 2:40: Persistence & Verification Proof
- **Action:** Refresh the browser page (<kbd>F5</kbd> or <kbd>Ctrl+R</kbd>).
- **Narrative:**
  > "Refreshing the page confirms that all sessions, task states, and plan versions persist in SQLite WAL storage. We tested session isolation, duplicate submissions, the no-key mentor mode, and the reload flow in a browser."
- **Screen:** Display repository `README.md` and test suite output.

