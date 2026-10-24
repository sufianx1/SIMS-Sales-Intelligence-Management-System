"""
app/services/inventory_service.py
---------------------------------
Business service for multi-store inventory operations, movements, transfers, and CSV exports.
"""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from app.db.mongo import get_db
from app.repositories.inventory_repo import InventoryRepository
from app.schemas.inventory import (
    InventoryItemResponse, InventoryAdjustRequest,
    InventoryReceiveRequest, InventoryTransferRequest,
    InventoryMovementResponse, InventoryAlertResponse,
    RebalanceRecommendationResponse
)


class InventoryService:

    @staticmethod
    def list_inventory(
        company_id: int,
        store_id: Optional[int] = None,
        category: Optional[str] = None,
        low_stock_only: bool = False,
        search: Optional[str] = None
    ) -> List[InventoryItemResponse]:
        items = InventoryRepository.list_inventory(
            company_id=company_id,
            store_id=store_id,
            category=category,
            low_stock_only=low_stock_only,
            search=search
        )
        return [InventoryItemResponse(**it) for it in items]

    @staticmethod
    def adjust_stock(company_id: int, data: InventoryAdjustRequest, user_id: int) -> InventoryItemResponse:
        db = get_db()
        # Verify store belongs to tenant
        st = db.stores.find_one({"company_id": company_id, "store_id": data.store_id})
        if not st:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Store #{data.store_id} not found in this company.")

        # Verify product belongs to tenant
        prod = db.products.find_one({"company_id": company_id, "product_id": data.product_id.strip()})
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{data.product_id}' not found in this company.")

        try:
            InventoryRepository.adjust_stock(
                company_id=company_id,
                store_id=data.store_id,
                product_id=data.product_id,
                quantity_change=data.quantity_change,
                reason=data.reason,
                performed_by=user_id
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # Return updated item
        updated_list = InventoryRepository.list_inventory(company_id=company_id, store_id=data.store_id, search=data.product_id)
        match = next((x for x in updated_list if x["product_id"] == data.product_id.strip()), None)
        if not match:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated inventory.")
        return InventoryItemResponse(**match)

    @staticmethod
    def receive_stock(company_id: int, data: InventoryReceiveRequest, user_id: int) -> InventoryItemResponse:
        db = get_db()
        st = db.stores.find_one({"company_id": company_id, "store_id": data.store_id})
        if not st:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Store #{data.store_id} not found in this company.")

        prod = db.products.find_one({"company_id": company_id, "product_id": data.product_id.strip()})
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{data.product_id}' not found in this company.")

        InventoryRepository.receive_stock(
            company_id=company_id,
            store_id=data.store_id,
            product_id=data.product_id,
            quantity=data.quantity,
            unit_cost=data.unit_cost,
            supplier=data.supplier,
            reason=data.reason,
            performed_by=user_id
        )

        updated_list = InventoryRepository.list_inventory(company_id=company_id, store_id=data.store_id, search=data.product_id)
        match = next((x for x in updated_list if x["product_id"] == data.product_id.strip()), None)
        return InventoryItemResponse(**match)

    @staticmethod
    def transfer_stock(company_id: int, data: InventoryTransferRequest, user_id: int) -> InventoryMovementResponse:
        db = get_db()
        if data.from_store_id == data.to_store_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Origin and destination stores must be different.")

        # Verify stores
        from_st = db.stores.find_one({"company_id": company_id, "store_id": data.from_store_id})
        to_st = db.stores.find_one({"company_id": company_id, "store_id": data.to_store_id})
        if not from_st or not to_st:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Origin or destination store does not belong to active company.")

        prod = db.products.find_one({"company_id": company_id, "product_id": data.product_id.strip()})
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{data.product_id}' not found in this company.")

        try:
            mov = InventoryRepository.transfer_stock(
                company_id=company_id,
                from_store_id=data.from_store_id,
                to_store_id=data.to_store_id,
                product_id=data.product_id,
                quantity=data.quantity,
                reason=data.reason,
                performed_by=user_id
            )
            return InventoryMovementResponse(
                movement_id=mov["movement_id"],
                company_id=company_id,
                from_store_id=data.from_store_id,
                from_store_name=from_st["store_name"],
                to_store_id=data.to_store_id,
                to_store_name=to_st["store_name"],
                product_id=data.product_id,
                product_name=prod["product_name"],
                quantity=data.quantity,
                movement_type="TRANSFER",
                reason=data.reason or "Inter-Store Stock Transfer",
                performed_by=user_id,
                timestamp=mov["timestamp"]
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    def list_movements(company_id: int, store_id: Optional[int] = None, product_id: Optional[str] = None, limit: int = 50) -> List[InventoryMovementResponse]:
        movements = InventoryRepository.list_movements(company_id=company_id, store_id=store_id, product_id=product_id, limit=limit)
        return [InventoryMovementResponse(**m) for m in movements]

    @staticmethod
    def get_alerts(company_id: int, store_id: Optional[int] = None) -> List[InventoryAlertResponse]:
        alerts = InventoryRepository.get_alerts(company_id=company_id, store_id=store_id)
        return [InventoryAlertResponse(**a) for a in alerts]

    @staticmethod
    def get_rebalance_recommendations(company_id: int, store_id: Optional[int] = None) -> List[RebalanceRecommendationResponse]:
        recs = InventoryRepository.get_rebalance_recommendations(company_id=company_id, store_id=store_id)
        return [RebalanceRecommendationResponse(**r) for r in recs]
