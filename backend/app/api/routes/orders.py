"""
app/api/routes/orders.py
------------------------
Endpoints for Order listing, multi-filter queries, and transactional creation/management.
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_tenant_context, require_permission
from app.schemas.auth import TenantContext
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderSummaryResponse, OrderDetailResponse
)
from app.schemas.common import PaginatedResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=PaginatedResponse[OrderSummaryResponse], status_code=status.HTTP_200_OK)
def list_orders(
    region: Optional[str] = Query(None, description="Filter by geographic region"),
    ship_mode: Optional[str] = Query(None, description="Filter by ship mode"),
    customer_id: Optional[str] = Query(None, description="Filter by customer code"),
    store_id: Optional[int] = Query(None, description="Filter by store ID"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search by order ID or customer name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    context: TenantContext = Depends(get_tenant_context)
):
    """
    Lists paginated orders for active tenant with aggregated line item revenue and metrics.
    If the current user has a store-level restriction, store_id filter is automatically enforced.
    """
    effective_store_id = context.store_id if context.store_id else store_id

    return OrderService.list_orders(
        company_id=context.company_id,
        store_id=effective_store_id,
        customer_id=customer_id,
        region=region,
        ship_mode=ship_mode,
        start_date=start_date,
        end_date=end_date,
        search=search,
        page=page,
        limit=limit
    )


@router.get("/{order_id}", response_model=OrderDetailResponse, status_code=status.HTTP_200_OK)
def get_order(order_id: str, context: TenantContext = Depends(get_tenant_context)):
    """
    Retrieves full order details including line items scoped to active tenant.
    """
    return OrderService.get_order_detail(context.company_id, order_id)


@router.post("", response_model=OrderDetailResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    context: TenantContext = Depends(require_permission("create_order"))
):
    """
    Creates an order and all constituent line items within an atomic database transaction.
    Guarantees cross-tenant integrity on Customer, Store, and Products (Requires create_order).
    """
    effective_store_id = context.store_id if context.store_id else data.store_id
    if effective_store_id != data.store_id:
        data.store_id = effective_store_id

    return OrderService.create_order(context.company_id, data)


@router.put("/{order_id}", response_model=OrderSummaryResponse, status_code=status.HTTP_200_OK)
def update_order(
    order_id: str,
    data: OrderUpdate,
    context: TenantContext = Depends(require_permission("manage_orders"))
):
    """
    Updates order dispatch and location information (Requires manage_orders permission).
    """
    return OrderService.update_order(context.company_id, order_id, data)


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
def delete_order(
    order_id: str,
    context: TenantContext = Depends(require_permission("manage_orders"))
):
    """
    Cancels and deletes an order and all line items (Requires manage_orders permission).
    """
    OrderService.delete_order(context.company_id, order_id)
    return {"detail": f"Order '{order_id}' successfully deleted."}
