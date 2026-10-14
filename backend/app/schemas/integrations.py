"""
app/schemas/integrations.py
---------------------------
Schemas for external connectors, data synchronization schedules,
and sync execution audit logs.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IntegrationResponse(BaseModel):
    integration_id: str
    company_id: int
    store_id: Optional[int] = None
    store_name: Optional[str] = None
    name: str
    connector_type: str  # POS_REST_API, ECOMMERCE_WEBHOOK, MOCK_STORE_CONNECTOR
    is_active: bool
    config: Dict[str, Any] = {}
    last_sync_at: Optional[str] = None
    sync_status: str  # SUCCESS, FAILED, PENDING, RUNNING
    created_at: str


class IntegrationCreate(BaseModel):
    name: str = Field(min_length=3)
    connector_type: str = Field(description="Connector type: POS_REST_API, ECOMMERCE_WEBHOOK, MOCK_STORE_CONNECTOR")
    store_id: Optional[int] = None
    config: Dict[str, Any] = {}


class SyncExecutionResponse(BaseModel):
    log_id: str
    integration_id: str
    status: str
    records_processed: int
    cursor_checkpoint: str
    started_at: str
    completed_at: str
    duration_seconds: float
    message: str
    errors: List[str] = []


class SyncLogItem(BaseModel):
    log_id: str
    integration_id: str
    company_id: int
    sync_type: str
    records_processed: int
    errors: List[str] = []
    status: str
    started_at: str
    completed_at: Optional[str] = None
    cursor_checkpoint: Optional[str] = None
