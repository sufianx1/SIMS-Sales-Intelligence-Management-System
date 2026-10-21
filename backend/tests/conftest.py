"""
backend/tests/conftest.py
-------------------------
Pytest configuration and shared test fixtures for backend test suite.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

# Clean up sys.path to prevent legacy root app.py collision
sys.path = [p for p in sys.path if str(Path(p).resolve()) != str(ROOT_DIR.resolve())]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure test suite runs strictly in isolated test engine, protecting dev/prod data
import os
os.environ["ENVIRONMENT"] = "testing"
os.environ["MONGODB_DB_NAME"] = "sims_test_db"
os.environ["USE_MOCK_MONGO"] = "true"

from app.main import app


@pytest.fixture(scope="session")
def client():
    """Provides a reusable FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client
