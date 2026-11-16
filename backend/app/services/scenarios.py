import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any
from ..schemas import ScenarioResultOut, ProgramComparisonRow

BASE_DIR = Path(__file__).resolve().parents[2]  # backend directory
DATA_DIR = BASE_DIR / "data"


def compare_historical_rank(
    conn: sqlite3.Connection,
    rank: int,
    cohort_key: str,
    rank_type: str = "CRL"
) -> ScenarioResultOut:
    if rank <= 0:
        raise ValueError("Rank must be a positive integer.")

    cursor = conn.cursor()

    # Load cohort metadata
    cursor.execute("""
    SELECT cohort_key, institution, program, year, round, quota, seat_category, gender_pool, rank_type, opening_rank, closing_rank, source_url, retrieved_at
    FROM cutoffs
    WHERE cohort_key = ?
    ORDER BY closing_rank ASC
    """, (cohort_key,))
    rows = cursor.fetchall()

    if not rows:
        raise ValueError(
            f"Unsupported scenario: Cohort '{cohort_key}' not found. "
            f"Currently supported cohort: 'nitt_crl_open_os_2024' (NIT Tiruchirappalli, Open Category, Gender-Neutral, Other State, JoSAA 2024)."
        )

    # Validate rank type
    expected_rank_type = rows[0]["rank_type"]
    if rank_type.strip().upper() != expected_rank_type.strip().upper():
        raise ValueError(
            f"Incompatible rank type: Selected cohort requires '{expected_rank_type}' (JEE Main Common Rank List). "
            f"Provided rank type '{rank_type}' cannot be mixed with open-seat CRL historical data."
        )

    comparison_rows: List[ProgramComparisonRow] = []
    for r in rows:
        closing = r["closing_rank"]
        opening = r["opening_rank"]
        if rank <= closing:
            status = "at_or_better"
            diff = closing - rank
        else:
            status = "outside"
            diff = rank - closing

        comparison_rows.append(ProgramComparisonRow(
            institution=r["institution"],
            program=r["program"],
            opening_rank=opening,
            closing_rank=closing,
            status=status,
            difference=diff
        ))

    disclaimer = (
        "Historical JoSAA 2024 Round 5 closing ranks comparison only. "
        "Cutoffs fluctuate each year based on applicant volume, exam difficulty, and seat quota changes. "
        "This comparison does NOT guarantee admission, predict future probability, or certify official eligibility."
    )

    first = rows[0]
    return ScenarioResultOut(
        rank=rank,
        cohort_key=cohort_key,
        cohort_name="NIT Tiruchirappalli (JoSAA 2024 Round 5)",
        year=first["year"],
        round=first["round"],
        rank_type=first["rank_type"],
        quota=first["quota"],
        seat_category=first["seat_category"],
        source_url=first["source_url"],
        retrieved_at=first["retrieved_at"],
        rows=comparison_rows,
        disclaimer=disclaimer
    )
