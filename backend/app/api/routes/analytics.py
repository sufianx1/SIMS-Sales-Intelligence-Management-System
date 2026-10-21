"""
app/api/routes/analytics.py
---------------------------
Multi-dimensional sales analytics and time-series trend endpoints.
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_tenant_context
from app.schemas.auth import TenantContext
from app.schemas.analytics import MonthlyTrendMetric, BusinessInsight
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/trends", response_model=List[MonthlyTrendMetric], status_code=status.HTTP_200_OK)
def get_monthly_trends(
    store_id: Optional[int] = Query(None, description="Optional store filter"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    context: TenantContext = Depends(get_tenant_context)
):
    """
    Returns monthly temporal revenue and profit trend curve scoped strictly to active tenant.
    """
    target_store = context.store_id if context.store_id else store_id
    return AnalyticsService.get_monthly_trends(
        company_id=context.company_id,
        store_id=target_store,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/insights", response_model=List[BusinessInsight], status_code=status.HTTP_200_OK)
def get_explainable_insights(
    store_id: Optional[int] = Query(None, description="Optional store filter"),
    context: TenantContext = Depends(get_tenant_context)
):
    """
    Returns explainable business insights (stockout risks, low margin categories, revenue concentration)
    with explicit explanations, supporting records, limitations, and actionable next steps.
    """
    target_store = context.store_id if context.store_id else store_id
    return AnalyticsService.get_explainable_insights(
        company_id=context.company_id,
        store_id=target_store
    )
