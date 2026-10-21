"""
app/services/analytics_service.py
---------------------------------
Business service for Dashboard KPIs and Analytics with MongoDB.
"""

from typing import Optional, List
from datetime import date
from app.repositories.analytics_repo import AnalyticsRepository
from app.schemas.analytics import (
    DashboardMetrics, DashboardCharts, CategoryMetric,
    RegionMetric, StoreSalesMetric, ProductSalesMetric, CustomerSalesMetric, MonthlyTrendMetric,
    BusinessInsight
)


class AnalyticsService:

    @staticmethod
    def get_dashboard_metrics(company_id: int, store_id: Optional[int] = None) -> DashboardMetrics:
        data = AnalyticsRepository.get_dashboard_metrics(company_id, store_id)
        return DashboardMetrics(**data)

    @staticmethod
    def get_dashboard_charts(company_id: int, store_id: Optional[int] = None) -> DashboardCharts:
        cat_sales = AnalyticsRepository.get_sales_by_category(company_id, store_id)
        cat_profit = AnalyticsRepository.get_profit_by_category(company_id, store_id)
        reg_data = AnalyticsRepository.get_sales_by_region(company_id, store_id)
        store_data = AnalyticsRepository.get_sales_by_store(company_id)
        top_p_data = AnalyticsRepository.get_top_products(company_id, store_id, limit=10)
        top_c_data = AnalyticsRepository.get_top_customers(company_id, store_id, limit=10)

        return DashboardCharts(
            sales_by_category=[CategoryMetric(**c) for c in cat_sales],
            profit_by_category=[CategoryMetric(**c) for c in cat_profit],
            sales_by_region=[RegionMetric(**r) for r in reg_data],
            sales_by_store=[StoreSalesMetric(**s) for s in store_data],
            top_products=[ProductSalesMetric(**p) for p in top_p_data],
            top_customers=[CustomerSalesMetric(**c) for c in top_c_data]
        )

    @staticmethod
    def get_monthly_trends(
        company_id: int,
        store_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[MonthlyTrendMetric]:
        data = AnalyticsRepository.get_monthly_trends(company_id, store_id, start_date, end_date)
        return [MonthlyTrendMetric(**m) for m in data]

    @staticmethod
    def get_explainable_insights(company_id: int, store_id: Optional[int] = None) -> List[BusinessInsight]:
        data = AnalyticsRepository.get_explainable_insights(company_id, store_id)
        return [BusinessInsight(**i) for i in data]
