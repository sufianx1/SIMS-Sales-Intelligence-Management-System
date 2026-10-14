"""
database/scripts/migrate.py
----------------------------
Enterprise migration runner for Microsoft SQL Server (SalesManagementDB).
Tracks applied migrations in `__SchemaMigrations` and applies pending SQL
migrations in sequential order with atomic transaction handling.
"""

import os
import sys
import time
import argparse
from pathlib import Path
import pyodbc

# Determine project root and load environment variables if python-dotenv available
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "database" / "migrations"


def get_connection_string():
    """Builds connection string from environment or standard local defaults."""
    server = os.getenv("DB_SERVER", "localhost")
    database = os.getenv("DB_NAME", "SalesManagementDB")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    trusted = os.getenv("DB_TRUSTED_CONNECTION", "true").lower() in ("true", "1", "yes")
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")

    if trusted or not user:
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
        )
    else:
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
        )


def ensure_migrations_table(cursor):
    """Ensures the __SchemaMigrations table exists."""
    sql = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '__SchemaMigrations')
    BEGIN
        CREATE TABLE __SchemaMigrations (
            MigrationID INT IDENTITY(1,1) PRIMARY KEY,
            Version VARCHAR(50) NOT NULL UNIQUE,
            Description NVARCHAR(255) NOT NULL,
            AppliedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
            ExecutionTimeMs INT NOT NULL
        );
    END
    """
    cursor.execute(sql)
    cursor.commit()


def get_applied_migrations(cursor):
    """Returns set of applied migration versions."""
    cursor.execute("SELECT Version FROM __SchemaMigrations ORDER BY MigrationID")
    return {row[0] for row in cursor.fetchall()}


def split_sql_batches(sql_text: str):
    """Splits SQL script on GO statements (ignoring case, whitespace)."""
    batches = []
    current_batch = []
    for line in sql_text.splitlines():
        if line.strip().upper() == "GO":
            batch_str = "\n".join(current_batch).strip()
            if batch_str:
                batches.append(batch_str)
            current_batch = []
        else:
            current_batch.append(line)
    final_batch = "\n".join(current_batch).strip()
    if final_batch:
        batches.append(final_batch)
    return batches


def run_migrations(dry_run=False):
    """Discovers and applies pending migrations."""
    conn_str = get_connection_string()
    print(f"Connecting to SQL Server with connection string: {conn_str.split(';')[1]};{conn_str.split(';')[2]}")
    
    try:
        conn = pyodbc.connect(conn_str)
    except Exception as e:
        print(f"ERROR: Could not connect to SQL Server: {e}")
        sys.exit(1)

    cursor = conn.cursor()
    ensure_migrations_table(cursor)
    applied = get_applied_migrations(cursor)

    migration_files = sorted(MIGRATIONS_DIR.glob("V*.sql"))
    if not migration_files:
        print(f"No migration files found in {MIGRATIONS_DIR}")
        return

    print(f"\nFound {len(migration_files)} migration script(s).")
    pending = []
    for mf in migration_files:
        parts = mf.stem.split("__", 1)
        version = parts[0]
        desc = parts[1].replace("_", " ") if len(parts) > 1 else ""
        if version in applied:
            print(f"  [ALREADY APPLIED] {mf.name}")
        else:
            print(f"  [PENDING]         {mf.name}")
            pending.append((mf, version, desc))

    if not pending:
        print("\nAll migrations are up to date.")
        conn.close()
        return

    if dry_run:
        print(f"\nDry run complete. {len(pending)} migration(s) pending.")
        conn.close()
        return

    print(f"\nApplying {len(pending)} pending migration(s)...")
    for mf, version, desc in pending:
        print(f"\n--> Applying {mf.name}...")
        with open(mf, "r", encoding="utf-8") as f:
            sql_content = f.read()

        batches = split_sql_batches(sql_content)
        start_time = time.time()
        
        try:
            for b_idx, batch in enumerate(batches, 1):
                if batch:
                    cursor.execute(batch)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            cursor.execute(
                "INSERT INTO __SchemaMigrations (Version, Description, ExecutionTimeMs) VALUES (?, ?, ?)",
                (version, desc, elapsed_ms)
            )
            conn.commit()
            print(f"    SUCCESS: {mf.name} applied in {elapsed_ms}ms")
        except Exception as e:
            conn.rollback()
            print(f"    FAILED: Migration {mf.name} encountered an error: {e}")
            print("    Transaction rolled back. Aborting further migrations.")
            conn.close()
            sys.exit(1)

    print("\nDatabase migration process completed successfully.")
    conn.close()


def show_status():
    """Prints status table of migrations."""
    conn_str = get_connection_string()
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    ensure_migrations_table(cursor)
    
    cursor.execute("SELECT Version, Description, AppliedAt, ExecutionTimeMs FROM __SchemaMigrations ORDER BY MigrationID")
    rows = cursor.fetchall()
    
    print("\nApplied Migrations in SalesManagementDB:")
    print("-" * 80)
    print(f"{'Version':<10} {'Description':<35} {'Applied At':<22} {'Elapsed (ms)':<10}")
    print("-" * 80)
    for r in rows:
        print(f"{r[0]:<10} {r[1]:<35} {str(r[2])[:19]:<22} {r[3]:<10}")
    print("-" * 80)
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SalesManagementDB Migration Runner")
    parser.add_argument("--status", action="store_true", help="Show migration status table")
    parser.add_argument("--dry-run", action="store_true", help="Report pending migrations without applying")
    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        run_migrations(dry_run=args.dry_run)
