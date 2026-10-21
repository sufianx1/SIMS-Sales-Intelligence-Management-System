"""
app/schemas/analytics.py
------------------------
Schemas for executive dashboard KPI metrics, charts, and multi-dimensional analytics.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_sales: float = 0.0
    total_profit: float = 0.0
    profit_margin: float = 0.0
    total_orders: int = 0
    average_order_value: float = 0.0
    total_units: int = 0
    total_customers: int = 0
    total_products: int = 0
    active_stores: int = 0
    inventory_on_hand: int = 0
    low_stock_items: int = 0
    out_of_stock_items: int = 0


class CategoryMetric(BaseModel):
    category: str
    total_sales: float
    total_profit: float


class RegionMetric(BaseModel):
    region: str
    total_sales: float
    total_profit: float


class StoreSalesMetric(BaseModel):
    store_id: Optional[int] = None
    store_name: str
    total_sales: float
    total_profit: float
    total_orders: int


class ProductSalesMetric(BaseModel):
    product_name: str
    total_sales: float


class CustomerSalesMetric(BaseModel):
    customer_name: str
    total_sales: float


class DashboardCharts(BaseModel):
    sales_by_category: List[CategoryMetric] = []
    profit_by_category: List[CategoryMetric] = []
    sales_by_region: List[RegionMetric] = []
    sales_by_store: List[StoreSalesMetric] = []
    top_products: List[ProductSalesMetric] = []
    top_customers: List[CustomerSalesMetric] = []


class MonthlyTrendMetric(BaseModel):
    month: str
    sales: float
    profit: float


class BreakdownMetric(BaseModel):
    label: str
    sales: float
    profit: float
    orders_count: int


class BusinessInsight(BaseModel):
    insight_id: str
    category: str
    severity: str
    title: str
    summary: str
    explanation: str
    supporting_data: Dict[str, Any]
    limitations: str
    recommended_action: str
