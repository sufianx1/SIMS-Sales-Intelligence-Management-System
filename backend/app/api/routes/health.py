"""
app/api/routes/health.py
------------------------
Health check endpoint reporting application and MongoDB database connectivity status.
"""

from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.db.mongo import get_db, is_mock_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def check_health():
    """
    Checks operational liveness and MongoDB connectivity.
    Safe output: Does not leak internal connection strings or credentials.
    Distinguishes live persistent MongoDB from in-memory mock.
    """
    mock_active = is_mock_db()
    db_status = "connected"
    try:
        db = get_db()
        db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"unreachable: {type(e).__name__}"

    return HealthResponse(
        status="healthy" if "connected" in db_status else "degraded",
        database=db_status,
        is_mock=mock_active
    )


@router.get("/ready", response_model=HealthResponse)
def check_readiness(response: Response):
    """
    Readiness probe verifying critical system dependencies before routing production traffic.
    Distinguishes live persistent MongoDB from in-memory mock.
    Returns HTTP 503 Service Unavailable when database connection is degraded
    or when in-memory mock is running while persistent database storage is required.
    """
    must_persist = settings.REQUIRE_PERSISTENT_DB or settings.ENVIRONMENT.lower() in ("production", "staging")
    mock_active = is_mock_db()

    if must_persist and mock_active:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="not_ready",
            database="unsupported: in-memory mock running when persistent database is required",
            is_mock=True
        )

    try:
        db = get_db()
        db.command("ping")
        return HealthResponse(
            status="ready",
            database="connected",
            is_mock=mock_active
        )
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="not_ready",
            database=f"unreachable: {type(e).__name__}",
            is_mock=mock_active
        )
