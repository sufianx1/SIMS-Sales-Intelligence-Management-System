"""
app/api/routes/stores.py
------------------------
Endpoints for Store administration scoped to active tenant.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_tenant_context, require_permission
from app.schemas.auth import TenantContext
from app.schemas.company import StoreCreate, StoreUpdate, StoreResponse
from app.services.company_service import CompanyService

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get("", response_model=List[StoreResponse], status_code=status.HTTP_200_OK)
def list_stores(context: TenantContext = Depends(get_tenant_context)):
    """
    Lists all stores belonging to the active tenant.
    """
    return CompanyService.list_stores(context.company_id)


@router.get("/{store_id}", response_model=StoreResponse, status_code=status.HTTP_200_OK)
def get_store(store_id: int, context: TenantContext = Depends(get_tenant_context)):
    """
    Retrieves a single store by ID belonging to active tenant.
    """
    return CompanyService.get_store(context.company_id, store_id)


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
def create_store(
    data: StoreCreate,
    context: TenantContext = Depends(require_permission("MANAGE_STORES"))
):
    """
    Creates a new store within active tenant (Requires MANAGE_STORES permission).
    """
    return CompanyService.create_store(context.company_id, data)


@router.put("/{store_id}", response_model=StoreResponse, status_code=status.HTTP_200_OK)
def update_store(
    store_id: int,
    data: StoreUpdate,
    context: TenantContext = Depends(require_permission("MANAGE_STORES"))
):
    """
    Updates a store within active tenant (Requires MANAGE_STORES permission).
    """
    return CompanyService.update_store(context.company_id, store_id, data)
