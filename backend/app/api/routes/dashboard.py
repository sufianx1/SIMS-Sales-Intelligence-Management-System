"""
app/api/routes/dashboard.py
---------------------------
Executive Dashboard endpoints for high-level KPI cards and summary distributions.
Supports company-wide consolidated view or store-specific filtering.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_tenant_context
from app.schemas.auth import TenantContext
from app.schemas.analytics import DashboardMetrics, DashboardCharts
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetrics, status_code=status.HTTP_200_OK)
def get_dashboard_metrics(
    store_id: Optional[int] = Query(None, description="Optional store filter. Defaults to consolidated company-wide if omitted or 0"),
    context: TenantContext = Depends(get_tenant_context)
):
    """
    Returns dashboard metrics (Sales, Profit, Margin, Orders, Units, Customers, Products, Active Stores, Inventory)
    scoped strictly to the active tenant.
    """
    target_store = context.store_id if context.store_id else store_id
    return AnalyticsService.get_dashboard_metrics(context.company_id, target_store)


@router.get("/charts", response_model=DashboardCharts, status_code=status.HTTP_200_OK)
def get_dashboard_charts(
    store_id: Optional[int] = Query(None, description="Optional store filter. Defaults to consolidated company-wide if omitted or 0"),
    context: TenantContext = Depends(get_tenant_context)
):
    """
    Returns category performance, regional distribution, store comparisons, top products, and top customers.
    """
    target_store = context.store_id if context.store_id else store_id
    return AnalyticsService.get_dashboard_charts(context.company_id, target_store)
