"""
app/services/product_service.py
-------------------------------
Business service for managing products and catalog queries with MongoDB.
"""

from typing import Optional
from fastapi import HTTPException, status
from app.db.mongo import get_db
from app.repositories.product_repo import ProductRepository
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductDetailResponse, ProductOrderLine
)
from app.schemas.common import PaginatedResponse


class ProductService:

    @staticmethod
    def list_products(
        company_id: int,
        search: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> PaginatedResponse[ProductResponse]:
        offset = (page - 1) * limit
        items_data, total = ProductRepository.list(
            company_id, search=search, category=category, offset=offset, limit=limit
        )
        items = [ProductResponse(**i) for i in items_data]
        return PaginatedResponse.create(items=items, total=total, page=page, limit=limit)

    @staticmethod
    def get_product_detail(company_id: int, product_id: str) -> ProductDetailResponse:
        prod_data = ProductRepository.get_by_id(company_id, product_id)
        if not prod_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found in this company."
            )
        history_data = ProductRepository.get_order_history(company_id, product_id, limit=50)
        return ProductDetailResponse(
            product=ProductResponse(**prod_data),
            recent_transactions=[ProductOrderLine(**h) for h in history_data]
        )

    @staticmethod
    def create_product(company_id: int, data: ProductCreate) -> ProductResponse:
        db = get_db()
        existing = db.products.find_one({"company_id": company_id, "product_id": data.product_id.strip()})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product SKU '{data.product_id}' already exists in this company."
            )
        ProductRepository.create(
            company_id, data.product_id, data.product_name, data.category, data.sub_category
        )
        return ProductResponse(
            product_id=data.product_id.strip(),
            product_name=data.product_name.strip(),
            category=data.category,
            sub_category=data.sub_category,
            company_id=company_id
        )

    @staticmethod
    def update_product(company_id: int, product_id: str, data: ProductUpdate) -> ProductResponse:
        prod_data = ProductRepository.get_by_id(company_id, product_id)
        if not prod_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in this company.")
        ProductRepository.update(
            company_id, product_id, data.product_name, data.category, data.sub_category
        )
        updated = ProductRepository.get_by_id(company_id, product_id)
        return ProductResponse(**updated)
