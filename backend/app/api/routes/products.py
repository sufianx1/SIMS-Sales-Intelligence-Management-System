"""
app/api/routes/products.py
--------------------------
Endpoints for Product catalog browsing, searching, and product performance.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_tenant_context, require_permission
from app.schemas.auth import TenantContext
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductDetailResponse
)
from app.schemas.common import PaginatedResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=PaginatedResponse[ProductResponse], status_code=status.HTTP_200_OK)
def list_products(
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    context: TenantContext = Depends(get_tenant_context)
):
    """
    Lists paginated products with aggregate sales statistics for active tenant.
    """
    return ProductService.list_products(
        company_id=context.company_id,
        search=search,
        category=category,
        page=page,
        limit=limit
    )


@router.get("/{product_id}", response_model=ProductDetailResponse, status_code=status.HTTP_200_OK)
def get_product(product_id: str, context: TenantContext = Depends(get_tenant_context)):
    """
    Retrieves product details and recent transaction order lines scoped to active tenant.
    """
    return ProductService.get_product_detail(context.company_id, product_id)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    context: TenantContext = Depends(require_permission("manage_products"))
):
    """
    Creates a new product SKU under active company (Requires manage_products permission).
    """
    return ProductService.create_product(context.company_id, data)


@router.put("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
def update_product(
    product_id: str,
    data: ProductUpdate,
    context: TenantContext = Depends(require_permission("manage_products"))
):
    """
    Updates product information under active company (Requires manage_products permission).
    """
    return ProductService.update_product(context.company_id, product_id, data)
