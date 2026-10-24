"""
app/api/routes/inventory.py
---------------------------
FastAPI route handlers for inventory management, stock adjustments,
inter-store transfers, movement history, and low-stock alerts.
"""

from typing import Optional, List, Any
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse
import io
import csv
from app.api.dependencies import get_tenant_context, require_permission
from app.schemas.auth import TenantContext
from app.schemas.inventory import (
    InventoryItemResponse, InventoryAdjustRequest,
    InventoryReceiveRequest, InventoryTransferRequest,
    InventoryMovementResponse, InventoryAlertResponse,
    RebalanceRecommendationResponse
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory Management"])


@router.get("", response_model=List[InventoryItemResponse], status_code=status.HTTP_200_OK)
def list_inventory(
    store_id: Optional[int] = Query(None, description="Optional store filter. Defaults to consolidated if omitted"),
    category: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    search: Optional[str] = Query(None),
    context: TenantContext = Depends(require_permission("view_inventory"))
):
    """
    Returns store-level or company-consolidated inventory levels.
    """
    target_store = context.store_id if context.store_id else store_id
    return InventoryService.list_inventory(
        company_id=context.company_id,
        store_id=target_store,
        category=category,
        low_stock_only=low_stock_only,
        search=search
    )


@router.post("/adjust", response_model=InventoryItemResponse, status_code=status.HTTP_200_OK)
def adjust_stock(
    data: InventoryAdjustRequest,
    context: TenantContext = Depends(require_permission("inventory_adjust"))
):
    """
    Records a manual inventory adjustment with traceable justification.
    """
    # If user has a restricted store_id, enforce it
    if context.store_id and context.store_id != data.store_id:
        data.store_id = context.store_id

    return InventoryService.adjust_stock(
        company_id=context.company_id,
        data=data,
        user_id=context.user_id
    )


@router.post("/receive", response_model=InventoryItemResponse, status_code=status.HTTP_200_OK)
def receive_stock(
    data: InventoryReceiveRequest,
    context: TenantContext = Depends(require_permission("inventory_adjust"))
):
    """
    Records incoming inventory receipts from purchase orders or suppliers.
    """
    if context.store_id and context.store_id != data.store_id:
        data.store_id = context.store_id

    return InventoryService.receive_stock(
        company_id=context.company_id,
        data=data,
        user_id=context.user_id
    )


@router.post("/transfer", response_model=InventoryMovementResponse, status_code=status.HTTP_200_OK)
def transfer_stock(
    data: InventoryTransferRequest,
    context: TenantContext = Depends(require_permission("inventory_transfer"))
):
    """
    Transfers inventory stock between two authorized stores with full audit logging.
    """
    return InventoryService.transfer_stock(
        company_id=context.company_id,
        data=data,
        user_id=context.user_id
    )


@router.get("/movements", response_model=List[InventoryMovementResponse], status_code=status.HTTP_200_OK)
def list_movements(
    store_id: Optional[int] = Query(None),
    product_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    context: TenantContext = Depends(require_permission("view_inventory"))
):
    """
    Returns the traceable inventory movements history (Receipts, Transfers, Adjustments).
    """
    target_store = context.store_id if context.store_id else store_id
    return InventoryService.list_movements(
        company_id=context.company_id,
        store_id=target_store,
        product_id=product_id,
        limit=limit
    )


@router.get("/alerts", response_model=List[InventoryAlertResponse], status_code=status.HTTP_200_OK)
def get_alerts(
    store_id: Optional[int] = Query(None),
    context: TenantContext = Depends(require_permission("view_inventory"))
):
    """
    Returns active low-stock and out-of-stock items requiring operational attention.
    """
    target_store = context.store_id if context.store_id else store_id
    return InventoryService.get_alerts(
        company_id=context.company_id,
        store_id=target_store
    )


@router.get("/rebalance-recommendations", response_model=List[RebalanceRecommendationResponse], status_code=status.HTTP_200_OK)
def get_rebalance_recommendations(
    store_id: Optional[int] = Query(None, description="Optional store filter"),
    context: TenantContext = Depends(require_permission("view_inventory"))
):
    """
    Returns explainable, deterministic inter-store inventory rebalancing recommendations.
    Identifies shortage stores and matches them with branches in the same company having surplus stock.
    """
    target_store = context.store_id if context.store_id else store_id
    return InventoryService.get_rebalance_recommendations(
        company_id=context.company_id,
        store_id=target_store
    )


@router.get("/export", response_class=PlainTextResponse)
def export_inventory_csv(
    store_id: Optional[int] = Query(None),
    context: TenantContext = Depends(require_permission("view_inventory"))
):
    """
    Exports inventory report as CSV. Sanitizes fields against CSV injection.
    """
    target_store = context.store_id if context.store_id else store_id
    items = InventoryService.list_inventory(company_id=context.company_id, store_id=target_store)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Store Name", "Product ID", "Product Name", "SKU", "Category",
        "Quantity On Hand", "Min Threshold", "Unit Cost", "Unit Price", "Valuation", "Status"
    ])

    for it in items:
        # Prevent formula injection: prefix with single quote if starts with =,+,-,@
        def sanitize(val: Any) -> str:
            s = str(val)
            if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
                return f"'{s}"
            return s

        writer.writerow([
            sanitize(it.store_name),
            sanitize(it.product_id),
            sanitize(it.product_name),
            sanitize(it.sku),
            sanitize(it.category),
            it.quantity_on_hand,
            it.min_threshold,
            f"{it.unit_cost:.2f}",
            f"{it.unit_price:.2f}",
            f"{it.valuation:.2f}",
            it.status
        ])

    return PlainTextResponse(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=inventory_report_company_{context.company_id}.csv"}
    )
