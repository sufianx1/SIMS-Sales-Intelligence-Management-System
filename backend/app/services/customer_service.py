"""
app/services/customer_service.py
--------------------------------
Business service for managing customers and customer order histories with MongoDB.
"""

from typing import Optional
from fastapi import HTTPException, status
from app.db.mongo import get_db
from app.repositories.customer_repo import CustomerRepository
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerDetailResponse, CustomerOrderLine
)
from app.schemas.common import PaginatedResponse


class CustomerService:

    @staticmethod
    def list_customers(
        company_id: int,
        search: Optional[str] = None,
        segment: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> PaginatedResponse[CustomerResponse]:
        offset = (page - 1) * limit
        items_data, total = CustomerRepository.list(
            company_id, search=search, segment=segment, offset=offset, limit=limit
        )
        items = [CustomerResponse(**i) for i in items_data]
        return PaginatedResponse.create(items=items, total=total, page=page, limit=limit)

    @staticmethod
    def get_customer_detail(company_id: int, customer_id: str) -> CustomerDetailResponse:
        cust_data = CustomerRepository.get_by_id(company_id, customer_id)
        if not cust_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer '{customer_id}' not found in this company."
            )
        history_data = CustomerRepository.get_order_history(company_id, customer_id, limit=50)
        return CustomerDetailResponse(
            customer=CustomerResponse(**cust_data),
            recent_orders=[CustomerOrderLine(**h) for h in history_data]
        )

    @staticmethod
    def create_customer(company_id: int, data: CustomerCreate) -> CustomerResponse:
        db = get_db()
        existing = db.customers.find_one({"company_id": company_id, "customer_id": data.customer_id.strip()})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer ID '{data.customer_id}' already exists in this company."
            )
        CustomerRepository.create(
            company_id, data.customer_id, data.customer_name, data.segment
        )
        return CustomerResponse(
            customer_id=data.customer_id.strip(),
            customer_name=data.customer_name.strip(),
            segment=data.segment,
            company_id=company_id
        )

    @staticmethod
    def update_customer(company_id: int, customer_id: str, data: CustomerUpdate) -> CustomerResponse:
        cust_data = CustomerRepository.get_by_id(company_id, customer_id)
        if not cust_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found in this company.")
        CustomerRepository.update(company_id, customer_id, data.customer_name, data.segment)
        updated = CustomerRepository.get_by_id(company_id, customer_id)
        return CustomerResponse(**updated)
