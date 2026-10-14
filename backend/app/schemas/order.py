"""
app/schemas/order.py
--------------------
Schemas for Orders and OrderDetails transactional operations.
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class OrderLineCreate(BaseModel):
    product_id: str = Field(min_length=1, max_length=20, description="Product SKU code")
    quantity: int = Field(ge=1, description="Quantity sold")
    sales: float = Field(ge=0.0, description="Total line sales amount")
    discount: float = Field(default=0.0, ge=0.0, le=1.0, description="Discount percentage (0.0 to 1.0)")
    profit: float = Field(description="Total line profit amount")


class OrderLineResponse(BaseModel):
    order_detail_id: int
    order_id: str
    product_id: str
    product_name: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    sales: float
    quantity: int
    discount: float
    profit: float


class OrderCreate(BaseModel):
    order_id: str = Field(min_length=3, max_length=20, description="Unique Order tracking code")
    order_date: date = Field(description="Transaction date")
    ship_date: Optional[date] = None
    ship_mode: Optional[str] = Field("Standard Class", max_length=50)
    customer_id: str = Field(min_length=1, max_length=20, description="Customer code")
    store_id: Optional[int] = Field(None, description="Store or branch ID")
    country: Optional[str] = Field("United States", max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    region: Optional[str] = Field(None, max_length=50)
    lines: List[OrderLineCreate] = Field(min_length=1, description="Order line items")


class OrderUpdate(BaseModel):
    ship_date: Optional[date] = None
    ship_mode: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=50)


class OrderSummaryResponse(BaseModel):
    order_id: str
    order_date: date
    ship_date: Optional[date] = None
    ship_mode: Optional[str] = None
    customer_id: str
    customer_name: str
    company_id: int
    store_id: Optional[int] = None
    store_name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    region: Optional[str] = None
    total_sales: float
    total_quantity: int
    total_profit: float
    line_count: int = 1


class OrderDetailResponse(BaseModel):
    order: OrderSummaryResponse
    lines: List[OrderLineResponse]
