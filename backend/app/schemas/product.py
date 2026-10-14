"""
app/schemas/product.py
----------------------
Schemas for Product catalog management and order line lookups.
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    product_id: str = Field(min_length=2, max_length=20, description="Unique product SKU")
    product_name: str = Field(min_length=2, max_length=255, description="Product description")
    category: Optional[str] = Field(None, max_length=50, description="Product Category")
    sub_category: Optional[str] = Field(None, max_length=50, description="Product Sub-Category")


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    sub_category: Optional[str] = Field(None, max_length=50)


class ProductResponse(BaseModel):
    product_id: str
    product_name: str
    category: Optional[str] = None
    sub_category: Optional[str] = None
    company_id: int
    total_sales: float = 0.0
    total_quantity: int = 0
    total_profit: float = 0.0


class ProductOrderLine(BaseModel):
    order_id: str
    order_date: date
    customer_name: str
    sales: float
    quantity: int
    discount: float
    profit: float


class ProductDetailResponse(BaseModel):
    product: ProductResponse
    recent_transactions: List[ProductOrderLine] = []
