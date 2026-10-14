"""
app/schemas/customer.py
-----------------------
Schemas for Customer directory and individual customer history.
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    customer_id: str = Field(min_length=2, max_length=20, description="Unique customer code")
    customer_name: str = Field(min_length=2, max_length=150, description="Customer display name")
    segment: Optional[str] = Field("Consumer", max_length=50, description="Market segment")


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, min_length=2, max_length=150)
    segment: Optional[str] = Field(None, max_length=50)


class CustomerResponse(BaseModel):
    customer_id: str
    customer_name: str
    segment: Optional[str] = None
    company_id: int
    total_orders: int = 0
    total_sales: float = 0.0
    total_profit: float = 0.0


class CustomerOrderLine(BaseModel):
    order_id: str
    order_date: date
    product_name: str
    category: Optional[str] = None
    sales: float
    quantity: int
    profit: float


class CustomerDetailResponse(BaseModel):
    customer: CustomerResponse
    recent_orders: List[CustomerOrderLine] = []
