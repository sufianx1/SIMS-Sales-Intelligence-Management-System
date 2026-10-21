"""
app/api/routes/integrations.py
------------------------------
FastAPI route handlers for external business integrations, connectors,
manual synchronization triggers, and sync audit logs.
"""

from typing import List
from fastapi import APIRouter, Depends, Query, Request, status
from app.api.dependencies import get_current_user, get_tenant_context, require_permission
from app.schemas.auth import UserProfile, TenantContext
from app.schemas.integrations import (
    IntegrationResponse, IntegrationCreate,
    SyncExecutionResponse, SyncLogItem
)
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/integrations", tags=["Integrations & Synchronization"])


@router.get("", response_model=List[IntegrationResponse], status_code=status.HTTP_200_OK)
def list_integrations(
    context: TenantContext = Depends(require_permission("manage_integrations"))
):
    """
    Lists external business connectors configured for the active company.
    """
    return IntegrationService.list_integrations(context.company_id)


@router.post("", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
def create_integration(
    data: IntegrationCreate,
    context: TenantContext = Depends(require_permission("manage_integrations"))
):
    """
    Configures a new external business system connector.
    """
    return IntegrationService.create_integration(context.company_id, data)


@router.patch("/{integration_id}/toggle", response_model=IntegrationResponse, status_code=status.HTTP_200_OK)
def toggle_integration(
    integration_id: str,
    is_active: bool = Query(...),
    context: TenantContext = Depends(require_permission("manage_integrations"))
):
    """
    Enables or disables an external connector.
    """
    return IntegrationService.toggle_integration(context.company_id, integration_id, is_active)


@router.post("/{integration_id}/sync", response_model=SyncExecutionResponse, status_code=status.HTTP_200_OK)
def trigger_synchronization(
    integration_id: str,
    current_user: UserProfile = Depends(get_current_user),
    context: TenantContext = Depends(require_permission("manage_integrations"))
):
    """
    Manually triggers incremental synchronization against the reference business connector.
    """
    return IntegrationService.trigger_sync(context.company_id, integration_id, current_user.user_id)


@router.get("/{integration_id}/logs", response_model=List[SyncLogItem], status_code=status.HTTP_200_OK)
def get_sync_logs(
    integration_id: str,
    context: TenantContext = Depends(require_permission("manage_integrations"))
):
    """
    Retrieves chronological synchronization logs and cursor checkpoints for a connector.
    """
    return IntegrationService.get_sync_logs(context.company_id, integration_id)


@router.post("/{integration_id}/webhook", status_code=status.HTTP_200_OK)
async def receive_webhook(
    integration_id: str,
    request: Request,
    context: TenantContext = Depends(get_tenant_context)
):
    """
    Ingests inbound event webhooks with constant-time HMAC signature verification,
    timestamp replay protection, and event deduplication.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    return IntegrationService.process_webhook(
        company_id=context.company_id,
        integration_id=integration_id,
        raw_body=raw_body,
        signature=signature,
        timestamp=timestamp
    )
