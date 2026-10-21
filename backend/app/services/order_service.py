"""
app/services/order_service.py
-----------------------------
Transactional business service for Orders and OrderDetails with strict tenant isolation via MongoDB.
"""

from typing import Optional
from datetime import date
from fastapi import HTTPException, status
from app.db.mongo import get_db
from app.repositories.order_repo import OrderRepository
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderSummaryResponse,
    OrderDetailResponse, OrderLineResponse
)
from app.schemas.common import PaginatedResponse


class OrderService:

    @staticmethod
    def list_orders(
        company_id: int,
        store_id: Optional[int] = None,
        customer_id: Optional[str] = None,
        region: Optional[str] = None,
        ship_mode: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> PaginatedResponse[OrderSummaryResponse]:
        offset = (page - 1) * limit
        items_data, total = OrderRepository.list(
            company_id=company_id,
            store_id=store_id,
            customer_id=customer_id,
            region=region,
            ship_mode=ship_mode,
            start_date=start_date,
            end_date=end_date,
            search=search,
            offset=offset,
            limit=limit
        )
        items = [OrderSummaryResponse(**i) for i in items_data]
        return PaginatedResponse.create(items=items, total=total, page=page, limit=limit)

    @staticmethod
    def get_order_detail(company_id: int, order_id: str) -> OrderDetailResponse:
        header_data = OrderRepository.get_by_id(company_id, order_id)
        if not header_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order '{order_id}' not found in this company."
            )
        lines_data = OrderRepository.get_lines(order_id, company_id=company_id)
        return OrderDetailResponse(
            order=OrderSummaryResponse(**header_data),
            lines=[OrderLineResponse(**line) for line in lines_data]
        )

    @staticmethod
    def create_order(company_id: int, data: OrderCreate) -> OrderDetailResponse:
        """
        Creates an order and all constituent line items.
        Enforces strict cross-tenant isolation on Customers, Stores, and Products.
        """
        db = get_db()

        # 1. Check duplicate OrderID
        if db.orders.find_one({"order_id": data.order_id.strip()}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order ID '{data.order_id}' already exists."
            )

        # 2. Enforce Customer belongs to CompanyID
        cust = db.customers.find_one({"company_id": company_id, "customer_id": data.customer_id.strip()})
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cross-Tenant Violation: Customer '{data.customer_id}' does not belong to active company."
            )

        # 3. Enforce Store belongs to CompanyID (if specified)
        if data.store_id:
            st = db.stores.find_one({"company_id": company_id, "store_id": int(data.store_id)})
            if not st:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cross-Tenant Violation: Store ID {data.store_id} does not belong to active company."
                )

        # 4. Enforce Products belong to CompanyID and snapshot authoritative financial fields
        lines_to_save = []
        for idx, line in enumerate(data.lines, 1):
            prod = db.products.find_one({"company_id": company_id, "product_id": line.product_id.strip()})
            if not prod:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cross-Tenant Violation: Line #{idx} Product '{line.product_id}' does not belong to active company."
                )

            unit_price = float(prod.get("unit_price", 0.0))
            unit_cost = float(prod.get("unit_cost", 0.0))
            qty = max(1, int(line.quantity))

            # Handle discount normalization (e.g., 0.10 or 10.0 -> 0.10)
            raw_discount = float(line.discount) if line.discount is not None else 0.0
            discount_rate = (raw_discount / 100.0) if raw_discount > 1.0 else max(0.0, raw_discount)

            # Determine authoritative line sales and profit
            if line.sales is not None and float(line.sales) > 0:
                line_sales = round(float(line.sales), 2)
            else:
                gross = round(unit_price * qty, 2)
                line_sales = round(gross * (1.0 - discount_rate), 2)

            cost_basis = round(unit_cost * qty, 2)
            line_profit = round(line_sales - cost_basis, 2)

            lines_to_save.append({
                "line_id": idx,
                "product_id": line.product_id.strip(),
                "product_name": prod.get("product_name", ""),
                "category": prod.get("category", ""),
                "sub_category": prod.get("sub_category", ""),
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "sales": line_sales,
                "quantity": qty,
                "discount": round(discount_rate, 4),
                "profit": line_profit
            })

        # 5. Insert order document into MongoDB
        OrderRepository.create_order(
            company_id=company_id,
            order_id=data.order_id,
            order_date=data.order_date,
            ship_date=data.ship_date,
            ship_mode=data.ship_mode,
            customer_id=data.customer_id,
            store_id=data.store_id,
            country=data.country,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            region=data.region,
            lines=lines_to_save
        )

        return OrderService.get_order_detail(company_id, data.order_id)

    @staticmethod
    def update_order(company_id: int, order_id: str, data: OrderUpdate) -> OrderSummaryResponse:
        existing = OrderRepository.get_by_id(company_id, order_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found in this company.")
        OrderRepository.update(
            company_id=company_id,
            order_id=order_id,
            ship_date=data.ship_date,
            ship_mode=data.ship_mode,
            city=data.city,
            state=data.state,
            region=data.region
        )
        updated = OrderRepository.get_by_id(company_id, order_id)
        return OrderSummaryResponse(**updated)

    @staticmethod
    def delete_order(company_id: int, order_id: str):
        existing = OrderRepository.get_by_id(company_id, order_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found in this company.")
        OrderRepository.delete(company_id, order_id)
