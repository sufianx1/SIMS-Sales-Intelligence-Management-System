"""
app/db/transactions.py
----------------------
Transaction context manager providing atomic commits and automatic rollbacks.
"""

from contextlib import contextmanager
from typing import Generator
import pyodbc
from app.db.connection import get_connection
from app.core.logging import logger


@contextmanager
def transaction() -> Generator[pyodbc.Cursor, None, None]:
    """
    Executes operations within an explicit database transaction.
    Commits on successful completion; automatically rolls back on any exception.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Transaction aborted and rolled back due to error: {e}")
        raise
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


atomic_transaction = transaction
