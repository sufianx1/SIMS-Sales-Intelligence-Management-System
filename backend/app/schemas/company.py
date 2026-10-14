"""
app/schemas/company.py
----------------------
Schemas for Companies (Tenants) and Stores.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=150, description="Company/Tenant name")


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=2, max_length=150)
    is_active: Optional[bool] = None


class CompanyResponse(BaseModel):
    company_id: int
    company_name: str
    is_active: bool
    created_at: Optional[datetime] = None


class StoreCreate(BaseModel):
    store_name: str = Field(min_length=2, max_length=150, description="Store or Branch name")
    location: Optional[str] = Field(None, max_length=255, description="Physical location or region")


class StoreUpdate(BaseModel):
    store_name: Optional[str] = Field(None, min_length=2, max_length=150)
    location: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class StoreResponse(BaseModel):
    store_id: int
    company_id: int
    store_name: str
    location: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
