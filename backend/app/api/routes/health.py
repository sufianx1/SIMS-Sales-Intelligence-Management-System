"""
app/api/routes/health.py
------------------------
Health check endpoint reporting application and MongoDB database connectivity status.
"""

from fastapi import APIRouter, Response, status
from app.db.mongo import get_db, is_mock_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def check_health():
    """
    Checks operational liveness and MongoDB connectivity.
    Safe output: Does not leak internal connection strings or credentials.
    """
    db_status = "connected"
    try:
        db = get_db()
        db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"unreachable: {type(e).__name__}"

    return HealthResponse(
        status="healthy" if "connected" in db_status else "degraded",
        database=db_status
    )


@router.get("/ready", response_model=HealthResponse)
def check_readiness(response: Response):
    """
    Readiness probe verifying critical system dependencies before routing production traffic.
    Returns HTTP 503 Service Unavailable when database connection is degraded.
    """
    try:
        db = get_db()
        db.command("ping")
        return HealthResponse(status="ready", database="connected")
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="not_ready", database=f"unreachable: {type(e).__name__}")
