"""
app/db/connection.py
--------------------
Database connection manager for Microsoft SQL Server using pyodbc.
Provides thread-safe connections and context managers for query execution.
"""

from contextlib import contextmanager
from typing import Generator
import pyodbc
from app.core.config import settings
from app.core.logging import logger


def get_connection() -> pyodbc.Connection:
    """
    Creates and returns a new active connection to SQL Server.
    Raises pyodbc.Error if connection fails.
    """
    try:
        conn = pyodbc.connect(settings.db_connection_string)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


@contextmanager
def get_db_connection() -> Generator[pyodbc.Connection, None, None]:
    """
    Context manager yielding a pyodbc connection, automatically closing it on exit.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


@contextmanager
def get_db_cursor() -> Generator[pyodbc.Cursor, None, None]:
    """
    Context manager yielding a pyodbc cursor and automatically closing connection.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            try:
                cursor.close()
            except Exception:
                pass
