"""
src/load_db.py
Loads generated CSVs into a SQLite database with strict schema, primary keys,
foreign keys, and indexes for high-performance querying.
"""

import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "ops.db")


def create_schema(cursor: sqlite3.Cursor):
    """Create relational schema with constraints and foreign keys."""
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Drop existing tables if recreating
    cursor.execute("DROP TABLE IF EXISTS sessions;")
    cursor.execute("DROP TABLE IF EXISTS shifts;")
    cursor.execute("DROP TABLE IF EXISTS operators;")
    
    # 1. Operators Table
    cursor.execute("""
    CREATE TABLE operators (
        operator_id TEXT PRIMARY KEY,
        region TEXT NOT NULL,
        join_date TEXT NOT NULL,
        tenure_days INTEGER NOT NULL,
        hourly_cost_usd REAL NOT NULL,
        primary_shift TEXT NOT NULL
    );
    """)
    
    # 2. Shifts Table
    cursor.execute("""
    CREATE TABLE shifts (
        shift_id TEXT PRIMARY KEY,
        operator_id TEXT NOT NULL,
        shift_date TEXT NOT NULL,
        shift_type TEXT NOT NULL,
        scheduled_hours REAL NOT NULL,
        active_hours REAL NOT NULL,
        FOREIGN KEY (operator_id) REFERENCES operators (operator_id)
    );
    """)
    
    # 3. Sessions Table
    cursor.execute("""
    CREATE TABLE sessions (
        session_id TEXT PRIMARY KEY,
        operator_id TEXT NOT NULL,
        session_date TEXT NOT NULL,
        start_hour_utc INTEGER NOT NULL,
        shift TEXT NOT NULL,
        task_type TEXT NOT NULL,
        robot_site_region TEXT NOT NULL,
        duration_min REAL NOT NULL,
        interventions INTEGER NOT NULL,
        latency_ms REAL NOT NULL,
        success INTEGER NOT NULL,
        quality_score INTEGER,
        data_accepted INTEGER NOT NULL,
        FOREIGN KEY (operator_id) REFERENCES operators (operator_id)
    );
    """)
    
    # Create indexes for fast joins, filters, and aggregations
    indexes = [
        "CREATE INDEX idx_operators_region ON operators(region);",
        "CREATE INDEX idx_operators_primary_shift ON operators(primary_shift);",
        "CREATE INDEX idx_shifts_operator_id ON shifts(operator_id);",
        "CREATE INDEX idx_shifts_shift_date ON shifts(shift_date);",
        "CREATE INDEX idx_shifts_shift_type ON shifts(shift_type);",
        "CREATE INDEX idx_sessions_operator_id ON sessions(operator_id);",
        "CREATE INDEX idx_sessions_session_date ON sessions(session_date);",
        "CREATE INDEX idx_sessions_shift ON sessions(shift);",
        "CREATE INDEX idx_sessions_task_type ON sessions(task_type);",
        "CREATE INDEX idx_sessions_success ON sessions(success);"
    ]
    for idx in indexes:
        cursor.execute(idx)


def load_data(conn: sqlite3.Connection):
    """Load CSVs from data/ directory into SQLite tables."""
    operators_csv = os.path.join(DATA_DIR, "operators.csv")
    shifts_csv = os.path.join(DATA_DIR, "shifts.csv")
    sessions_csv = os.path.join(DATA_DIR, "sessions.csv")
    
    for path in [operators_csv, shifts_csv, sessions_csv]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required CSV file: {path}. Run src/generate_data.py first.")
            
    # Load Operators
    df_operators = pd.read_csv(operators_csv)
    df_operators.to_sql("operators", conn, if_exists="append", index=False)
    print(f"Loaded {len(df_operators):,} rows into 'operators'")
    
    # Load Shifts
    df_shifts = pd.read_csv(shifts_csv)
    df_shifts.to_sql("shifts", conn, if_exists="append", index=False)
    print(f"Loaded {len(df_shifts):,} rows into 'shifts'")
    
    # Load Sessions
    df_sessions = pd.read_csv(sessions_csv)
    df_sessions.to_sql("sessions", conn, if_exists="append", index=False)
    print(f"Loaded {len(df_sessions):,} rows into 'sessions'")


def verify_db(conn: sqlite3.Connection):
    """Run verification checks on the loaded database."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    fk_errors = cursor.fetchall()
    if fk_errors:
        raise ValueError(f"Foreign key violations found: {fk_errors}")
        
    print("Database integrity check passed: 0 foreign key violations.")
    
    # Check table row counts
    counts = {}
    for table in ["operators", "shifts", "sessions"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]
        print(f"Table '{table}': {counts[table]:,} records verified.")


def main():
    print("=" * 60)
    print(f"Initializing SQLite Database at: {DB_PATH}")
    print("=" * 60)
    
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass
            
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        create_schema(cursor)
        load_data(conn)
        conn.commit()
        verify_db(conn)
        print("=" * 60)
        print("Database successfully built and verified!")
        print("=" * 60)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

