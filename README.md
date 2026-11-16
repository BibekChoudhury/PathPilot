# PathPilot: JEE Physics Study Replanner

A VibeX Codes Track 4 student mentor prototype. Take a nine-question diagnostic across three physics skills, get a study plan, and ask the mentor to fit it to a shorter time budget. Complete a separate three-question practice set to update the plan. The optional college panel compares an entered JEE Main CRL against three published historical program cutoffs.

## Run locally

Use Python 3.11+ and Node.js 18+ (tested here with Python 3.14 and Node.js 24). From the project root:

~~~text
python -m pip install -r backend/requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
python run.py
~~~

Open [the local app](http://127.0.0.1:8000). Rebuild the frontend after changing React code. For frontend development, keep FastAPI running on port 8000 and use `npm --prefix frontend run dev`; open the Vite URL on port 5173.

No account or model key is required. Copy `.env.example` to `.env` only when overriding configuration:

| Variable | Purpose |
|---|---|
| `HOST`, `PORT` | Default to `127.0.0.1` and `8000`. |
| `SQLITE_DB_PATH` | Defaults to `backend/pathpilot.db`. Keep the database on a persistent disk when hosting. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Set both to enable optional Gemini routing for free-form topic questions. The model selects a reviewed note. Common commands run through rules and the model cannot write to the database. |
| `COOKIE_SECURE` | Set to `1` on hosted HTTPS. Forward the public host and scheme from the trusted reverse proxy. |

## Verify

~~~text
python -m pytest backend/tests/test_core.py -q
python -m backend.tests.run_acceptance_checks
~~~

The acceptance runner covers API and static serving checks. Phone layout, keyboard use and a clean setup on another machine require separate verification. See [the review report](REVIEW_REPORT.md) for the checks run in this workspace.

## Demo and submission

Follow [the demo script](docs/demo-script.md) and use the [slide outline](docs/presentation-deck.md) or [HTML draft](docs/presentation-deck.html). Add the actual repository and demo links and export the required PPT/PDF before submitting. The source folder reviewed here was not a Git repository.

[Data sources](DATA_SOURCES.md) document the historical cohort and question bank. [Limitations](docs/limitations.md) describe future work. The demo estimates neither admissions probability nor exam readiness.
