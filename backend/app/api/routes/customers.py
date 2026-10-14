"""
app/api/routes/customers.py
--------------------------
Endpoints for Customer directory, search, metrics, and purchase history.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_tenant_context, require_permission
from app.schemas.auth import TenantContext
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerDetailResponse
)
from app.schemas.common import PaginatedResponse
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=PaginatedResponse[CustomerResponse], status_code=status.HTTP_200_OK)
def list_customers(
    search: Optional[str] = Query(None, description="Search by customer name or code"),
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    context: TenantContext = Depends(get_tenant_context)
):
    """
    Lists paginated customers with aggregated lifetime sales metrics for active tenant.
    """
    return CustomerService.list_customers(
        company_id=context.company_id,
        search=search,
        segment=segment,
        page=page,
        limit=limit
    )


@router.get("/{customer_id}", response_model=CustomerDetailResponse, status_code=status.HTTP_200_OK)
def get_customer(customer_id: str, context: TenantContext = Depends(get_tenant_context)):
    """
    Retrieves customer details and recent order history scoped strictly to active tenant.
    """
    return CustomerService.get_customer_detail(context.company_id, customer_id)


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    context: TenantContext = Depends(require_permission("CREATE_CUSTOMER"))
):
    """
    Creates a new customer record under the active company (Requires CREATE_CUSTOMER permission).
    """
    return CustomerService.create_customer(context.company_id, data)


@router.put("/{customer_id}", response_model=CustomerResponse, status_code=status.HTTP_200_OK)
def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    context: TenantContext = Depends(require_permission("UPDATE_CUSTOMER"))
):
    """
    Updates a customer record under the active company (Requires UPDATE_CUSTOMER permission).
    """
    return CustomerService.update_customer(context.company_id, customer_id, data)
