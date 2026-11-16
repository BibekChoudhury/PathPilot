# PathPilot data sources

- **Physics questions and notes:** 18 authored questions in `backend/data/questions.json`, three diagnostic and three practice items per skill. The reviewed implementation separates the sets and counts the first answer to each question. Verify the question content with a subject reviewer before using it beyond the demo. Misconception tags suggest possible explanations. They do not establish the cause of a wrong answer.
- **Historical ranks:** [JoSAA 2024 Round 5 table for NIT Tiruchirappalli, PDF mirror](https://static.collegedekho.com/media/django-summernote/2024-07-18/6829e64b-86f2-415e-93e2-9661bed006ac.pdf), cross-checked on 15 November 2026. For additional years and cohorts see [JoSAA opening and closing ranks](https://josaa.nic.in/or-cr/).

The rank panel supports only **JEE Main CRL, Other State, OPEN, gender-neutral, JoSAA 2024 Round 5**. The included rows are all four-year B.Tech programmes at NIT Tiruchirappalli.

| Programme | Opening rank | Closing rank |
|---|---:|---:|
| Computer Science and Engineering | 299 | 1224 |
| Electronics and Communication Engineering | 917 | 3546 |
| Electrical and Electronics Engineering | 3029 | 6040 |

These are historical thresholds. A numerically smaller or equal rank meets that threshold. The prototype does not assess eligibility, project a student's rank, or estimate admission probability.
