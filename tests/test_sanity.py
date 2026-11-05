"""
tests/test_sanity.py
Pytest sanity suite for Teleoperation Ops Dashboard.
Tests data validity, integrity, constraints, foreign keys, and SQL query execution.
"""

import os
import sqlite3
import pandas as pd
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "ops.db")
MEMO_PATH = os.path.join(BASE_DIR, "reports", "ops_memo.md")


@pytest.fixture(scope="session")
def db_conn():
    """Fixture providing an active SQLite connection to ops.db."""
    assert os.path.exists(DB_PATH), f"Database not found at {DB_PATH}. Run load_db.py first."
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def datasets():
    """Fixture loading the raw CSV files into pandas DataFrames."""
    operators_csv = os.path.join(DATA_DIR, "operators.csv")
    sessions_csv = os.path.join(DATA_DIR, "sessions.csv")
    shifts_csv = os.path.join(DATA_DIR, "shifts.csv")

    assert os.path.exists(operators_csv), f"Missing {operators_csv}"
    assert os.path.exists(sessions_csv), f"Missing {sessions_csv}"
    assert os.path.exists(shifts_csv), f"Missing {shifts_csv}"

    return {
        "operators": pd.read_csv(operators_csv),
        "sessions": pd.read_csv(sessions_csv),
        "shifts": pd.read_csv(shifts_csv),
    }


def test_row_counts(datasets):
    """Verify row counts fall within expected simulated ranges."""
    operators = datasets["operators"]
    sessions = datasets["sessions"]
    shifts = datasets["shifts"]

    assert 140 <= len(operators) <= 160, f"Unexpected operator count: {len(operators)}"
    assert 10000 <= len(sessions) <= 14000, f"Unexpected session count: {len(sessions)}"
    assert 5000 <= len(shifts) <= 10000, f"Unexpected shift count: {len(shifts)}"


def test_no_null_primary_keys(datasets):
    """Verify that there are no null IDs in any table."""
    for table_name, id_col in [
        ("operators", "operator_id"),
        ("sessions", "session_id"),
        ("shifts", "shift_id"),
    ]:
        df = datasets[table_name]
        assert id_col in df.columns, f"Missing {id_col} in {table_name}"
        assert df[id_col].isnull().sum() == 0, f"Null IDs detected in {table_name}.{id_col}"
        assert df[id_col].nunique() == len(df), f"Duplicate IDs detected in {table_name}.{id_col}"


def test_foreign_key_integrity(db_conn, datasets):
    """Verify foreign key references between sessions/shifts and operators."""
    # SQLite PRAGMA check
    cursor = db_conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    violations = cursor.fetchall()
    assert len(violations) == 0, f"Foreign key violations detected in SQLite: {violations}"

    # Pandas set difference check
    valid_op_ids = set(datasets["operators"]["operator_id"])
    assert set(datasets["sessions"]["operator_id"]).issubset(valid_op_ids)
    assert set(datasets["shifts"]["operator_id"]).issubset(valid_op_ids)


def test_success_binary_values(datasets):
    """Verify success values are strictly 0 or 1."""
    sessions = datasets["sessions"]
    assert set(sessions["success"].unique()).issubset({0, 1})
    assert sessions["success"].isnull().sum() == 0


def test_latency_positive(datasets):
    """Verify network latency is strictly positive."""
    sessions = datasets["sessions"]
    assert (sessions["latency_ms"] > 0).all(), "Found non-positive latency values"
    assert (sessions["latency_ms"] < 1000).all(), "Found unrealistically high latency (>1000ms)"


def test_utilization_range(datasets):
    """Verify shift utilization (active_hours / scheduled_hours) is between 0.0 and 1.2."""
    shifts = datasets["shifts"]
    assert (shifts["scheduled_hours"] > 0).all()
    assert (shifts["active_hours"] >= 0).all()

    utilization = shifts["active_hours"] / shifts["scheduled_hours"]
    assert (utilization >= 0.0).all(), "Found negative utilization"
    assert (utilization <= 1.2).all(), f"Found utilization exceeding 1.2: max={utilization.max()}"


def test_quality_score_and_data_accepted(datasets):
    """Verify quality_score and data_accepted constraints."""
    sessions = datasets["sessions"]
    # data_accepted must be strictly binary
    assert set(sessions["data_accepted"].unique()).issubset({0, 1})

    # quality_score when present must be integer between 1 and 5
    qa_present = sessions["quality_score"].dropna()
    assert len(qa_present) > 0, "No QA quality scores found"
    assert qa_present.isin([1, 2, 3, 4, 5]).all(), "Quality scores must be integers 1 to 5"


def test_sql_queries_execute(db_conn):
    """Verify all queries in sql/queries.sql execute cleanly and return non-empty datasets."""
    from src.analysis import parse_queries

    queries = parse_queries()
    assert len(queries) >= 10, f"Expected at least 10 named queries, found {len(queries)}"

    for name, sql in queries.items():
        df = pd.read_sql_query(sql, db_conn)
        assert len(df) > 0, f"Query '{name}' returned 0 rows"


def test_memo_exists_and_valid():
    """Verify reports/ops_memo.md exists, has executive summary and 3 recommendations."""
    assert os.path.exists(MEMO_PATH), f"Ops memo file does not exist at {MEMO_PATH}"
    with open(MEMO_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Executive Summary" in content
    assert "Recommendation 1" in content
    assert "Recommendation 2" in content
    assert "Recommendation 3" in content
    assert "Expected Impact (Estimate)" in content
    assert "SYNTHETIC DATA FOR PORTFOLIO DEMONSTRATION ONLY" in content

