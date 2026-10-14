"""
app/schemas/inventory.py
------------------------
Schemas for multi-store inventory levels, stock adjustments, store transfers,
traceable movements, and low-stock alerts.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class InventoryItemResponse(BaseModel):
    inventory_id: str
    company_id: int
    store_id: int
    store_name: str
    product_id: str
    product_name: str
    category: str
    sku: str
    quantity_on_hand: int
    min_threshold: int
    max_threshold: int
    unit_cost: float
    unit_price: float
    valuation: float
    status: str  # "IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"
    last_updated: Optional[str] = None


class ConsolidatedInventoryItem(BaseModel):
    product_id: str
    product_name: str
    category: str
    sku: str
    total_quantity: int
    total_valuation: float
    store_breakdown: List[dict] = []
    status: str


class InventoryAdjustRequest(BaseModel):
    store_id: int = Field(gt=0, description="Store where adjustment occurs")
    product_id: str = Field(min_length=1)
    quantity_change: int = Field(description="Can be positive (addition) or negative (shrinkage/damage)")
    reason: str = Field(min_length=3, description="Justification for adjustment")


class InventoryReceiveRequest(BaseModel):
    store_id: int = Field(gt=0)
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_cost: Optional[float] = None
    supplier: Optional[str] = None
    reason: Optional[str] = "Purchase Order Receipt"


class InventoryTransferRequest(BaseModel):
    from_store_id: int = Field(gt=0, description="Origin store")
    to_store_id: int = Field(gt=0, description="Destination store")
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0, description="Quantity to transfer")
    reason: Optional[str] = "Inter-Store Stock Rebalance"


class InventoryMovementResponse(BaseModel):
    movement_id: str
    company_id: int
    from_store_id: Optional[int] = None
    from_store_name: Optional[str] = None
    to_store_id: Optional[int] = None
    to_store_name: Optional[str] = None
    product_id: str
    product_name: str
    quantity: int
    movement_type: str  # RECEIPT, ADJUSTMENT, TRANSFER, SALE
    reason: str
    performed_by: Optional[int] = None
    timestamp: str


class InventoryAlertResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    store_id: int
    store_name: str
    quantity_on_hand: int
    min_threshold: int
    severity: str  # "WARNING" (low) or "CRITICAL" (out of stock)
