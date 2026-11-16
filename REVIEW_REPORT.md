# PathPilot review and fixes

Reviewed 15 November 2026 in `C:\Users\BibekC\Downloads\vibexcddoe`. I applied the fixes to this project folder. Scope: the VibeX Codes demo and submission readiness, with particular attention to the student journey and what the project actually demonstrates.

| Finding | Fix |
|---|---|
| Opening the diagnostic or practice again made a new assessment; repeated work could inflate evidence. | Resume the saved assessment, use first attempts as evidence, exclude skips, and prevent repeat grading. The mentor and practice screen now use the same assessment. |
| Answer retries could report a completed assessment prematurely, and answer/result writes could commit separately. | Grade only the current assigned item, reject conflicting submissions, and commit the answer and idempotency record together. |
| Deferred tasks disappeared on reload and the replan diff loaded the newly written plan as the previous plan. | Persist deferred tasks, compare to the actual prior plan, and serialize version checks and writes. |
| Finishing practice didn't update the plan and the final screen never appeared. | Show completion, keep practice evidence separate, and recalculate the current plan once after final practice submission. |
| Mentor changed plans for unrelated mentions of minutes and claimed AI was active with only a configured key. | Use explicit commands for writes and keep previews read-only. Optional Gemini routing can only select a reviewed concept note; a run shows Gemini mode only if its response was used. |
| Historical values and portfolio-style verification claims were unsupported. | Replace rank values with three checked NIT Tiruchirappalli programme rows; use the same data for panel and mentor; correct README/deck/sample scripts and remove unverified timings. |
| Frontend used utility classes without a build step; auth stored the bearer in local storage. | Compile Tailwind locally, restore responsive styles and focus indicators, and use the HttpOnly session cookie for the browser. Enforce expiry and same-origin browser writes. |
| App configuration loaded after database imports, and standalone serving guessed arbitrary files. | Load environment first, serve the compiled SPA and static assets explicitly, and document the clean setup commands. |

**Test evidence**

- Backend pytest: 14 passed. Tests covered restart/resume at the API boundary, answer replay, session isolation and expiry, mentor preview, stale versions, plan persistence, historical rank validation, and mocked Gemini success and timeout.
- Acceptance runner: 9 automated checks passed. It now calls out the separate manual browser check.
- Browser against the local app: submitted a diagnostic answer by keyboard, reloaded at question 2, finished the quiz, and created plan v1. The mentor saved a 30-minute plan v2 with three deferred tasks; those survived reload. Mentor-launched practice reached its completion screen and produced plan v3. Checked the corrected historical comparison at 390 px wide.
- TypeScript/Vite production build completed with compiled responsive styles.

**Remaining before submission**

1. This folder was not a Git repository. Publish the tested source to the team's GitHub/GitLab repo and confirm a signed-out judge can open the link.
2. Insert actual project/demo links in the slide deck, then export and check an 8–10 slide PDF or PPT. The nine-slide HTML draft is available; no PDF/PPT or submitted entry was verified during this review.
3. If you want to demonstrate optional Gemini topic routing, set `GEMINI_API_KEY` and `GEMINI_MODEL` and perform a live smoke test. Success and failure were verified with mocks; the built-in mentor actions were verified live without a key. Leave the optional provider off for a dependable keyless demo.
4. Treat the three skills and the single JoSAA cohort as a prototype. A full syllabus, multi-day scheduler, production access controls and calibrated forecasts are future work.

Cutoff source: [JoSAA 2024 Round 5 table for NIT Tiruchirappalli (PDF mirror)](https://static.collegedekho.com/media/django-summernote/2024-07-18/6829e64b-86f2-415e-93e2-9661bed006ac.pdf).
