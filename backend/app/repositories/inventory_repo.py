"""
app/repositories/inventory_repo.py
----------------------------------
MongoDB repository for multi-store inventory levels, stock adjustments,
traceable inter-store transfers, and inventory movement audit logs.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
from pymongo.database import Database
from app.db.mongo import get_db


class InventoryRepository:

    @staticmethod
    def list_inventory(
        company_id: int,
        store_id: Optional[int] = None,
        category: Optional[str] = None,
        low_stock_only: bool = False,
        search: Optional[str] = None,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        filter_doc: Dict[str, Any] = {"company_id": company_id}
        if store_id is not None and store_id != 0:
            filter_doc["store_id"] = int(store_id)

        stores_map = {s["store_id"]: s["store_name"] for s in database.stores.find({"company_id": company_id})}
        products_cursor = database.products.find({"company_id": company_id})
        products_map = {p["product_id"]: p for p in products_cursor}

        cursor = database.inventory.find(filter_doc)
        results = []

        for item in cursor:
            prod_id = item["product_id"]
            prod = products_map.get(prod_id, {})
            p_cat = prod.get("category", "General")
            p_name = prod.get("product_name", prod_id)
            p_sku = prod.get("sku", prod_id)
            cost = float(prod.get("unit_cost", 0.0))
            price = float(prod.get("unit_price", 0.0))

            if category and category != "All" and p_cat.lower() != category.lower():
                continue

            if search:
                s_lower = search.strip().lower()
                if s_lower not in p_name.lower() and s_lower not in prod_id.lower() and s_lower not in p_sku.lower():
                    continue

            qty = int(item.get("quantity_on_hand", 0))
            min_thresh = int(item.get("min_threshold", 5))
            max_thresh = int(item.get("max_threshold", 100))

            if qty == 0:
                status = "OUT_OF_STOCK"
            elif qty <= min_thresh:
                status = "LOW_STOCK"
            else:
                status = "IN_STOCK"

            if low_stock_only and status == "IN_STOCK":
                continue

            results.append({
                "inventory_id": item["inventory_id"],
                "company_id": company_id,
                "store_id": item["store_id"],
                "store_name": stores_map.get(item["store_id"], f"Store #{item['store_id']}"),
                "product_id": prod_id,
                "product_name": p_name,
                "category": p_cat,
                "sku": p_sku,
                "quantity_on_hand": qty,
                "min_threshold": min_thresh,
                "max_threshold": max_thresh,
                "unit_cost": cost,
                "unit_price": price,
                "valuation": round(qty * cost, 2),
                "status": status,
                "last_updated": item.get("last_updated")
            })

        return sorted(results, key=lambda x: (x["product_name"], x["store_id"]))

    @staticmethod
    def adjust_stock(
        company_id: int,
        store_id: int,
        product_id: str,
        quantity_change: int,
        reason: str,
        performed_by: Optional[int] = None,
        db: Optional[Database] = None
    ) -> Dict[str, Any]:
        database = db if db is not None else get_db()
        now = datetime.now(timezone.utc).isoformat()

        inv = database.inventory.find_one({"company_id": company_id, "store_id": store_id, "product_id": product_id.strip()})
        current_qty = inv.get("quantity_on_hand", 0) if inv else 0
        new_qty = current_qty + quantity_change
        if new_qty < 0:
            raise ValueError(f"Cannot adjust inventory below zero. Current stock is {current_qty}, change requested is {quantity_change}.")

        inv_id = f"{company_id}-{store_id}-{product_id.strip()}"
        doc = {
            "inventory_id": inv_id,
            "company_id": company_id,
            "store_id": store_id,
            "product_id": product_id.strip(),
            "quantity_on_hand": new_qty,
            "min_threshold": inv.get("min_threshold", 5) if inv else 5,
            "max_threshold": inv.get("max_threshold", 100) if inv else 100,
            "last_updated": now
        }
        database.inventory.update_one(
            {"company_id": company_id, "store_id": store_id, "product_id": product_id.strip()},
            {"$set": doc},
            upsert=True
        )

        # Record movement
        mov_id = f"MOV-{uuid.uuid4().hex[:8].upper()}"
        movement_doc = {
            "movement_id": mov_id,
            "company_id": company_id,
            "from_store_id": store_id if quantity_change < 0 else None,
            "to_store_id": store_id if quantity_change > 0 else None,
            "product_id": product_id.strip(),
            "quantity": quantity_change,
            "movement_type": "ADJUSTMENT",
            "reason": reason,
            "performed_by": performed_by,
            "timestamp": now
        }
        database.inventory_movements.insert_one(movement_doc)
        return doc

    @staticmethod
    def receive_stock(
        company_id: int,
        store_id: int,
        product_id: str,
        quantity: int,
        unit_cost: Optional[float] = None,
        supplier: Optional[str] = None,
        reason: Optional[str] = None,
        performed_by: Optional[int] = None,
        db: Optional[Database] = None
    ) -> Dict[str, Any]:
        database = db if db is not None else get_db()
        now = datetime.now(timezone.utc).isoformat()

        inv = database.inventory.find_one({"company_id": company_id, "store_id": store_id, "product_id": product_id.strip()})
        current_qty = inv.get("quantity_on_hand", 0) if inv else 0
        new_qty = current_qty + quantity

        inv_id = f"{company_id}-{store_id}-{product_id.strip()}"
        doc = {
            "inventory_id": inv_id,
            "company_id": company_id,
            "store_id": store_id,
            "product_id": product_id.strip(),
            "quantity_on_hand": new_qty,
            "min_threshold": inv.get("min_threshold", 5) if inv else 5,
            "max_threshold": inv.get("max_threshold", 100) if inv else 100,
            "last_updated": now
        }
        database.inventory.update_one(
            {"company_id": company_id, "store_id": store_id, "product_id": product_id.strip()},
            {"$set": doc},
            upsert=True
        )

        # Update product unit_cost if provided
        if unit_cost is not None and unit_cost > 0:
            database.products.update_one(
                {"company_id": company_id, "product_id": product_id.strip()},
                {"$set": {"unit_cost": float(unit_cost)}}
            )

        # Record movement
        mov_id = f"MOV-{uuid.uuid4().hex[:8].upper()}"
        movement_doc = {
            "movement_id": mov_id,
            "company_id": company_id,
            "from_store_id": None,
            "to_store_id": store_id,
            "product_id": product_id.strip(),
            "quantity": quantity,
            "movement_type": "RECEIPT",
            "reason": f"Supplier Receipt: {supplier or 'Standard PO'} - {reason or ''}".strip(" -"),
            "performed_by": performed_by,
            "timestamp": now
        }
        database.inventory_movements.insert_one(movement_doc)
        return doc

    @staticmethod
    def transfer_stock(
        company_id: int,
        from_store_id: int,
        to_store_id: int,
        product_id: str,
        quantity: int,
        reason: Optional[str] = None,
        performed_by: Optional[int] = None,
        db: Optional[Database] = None
    ) -> Dict[str, Any]:
        database = db if db is not None else get_db()
        now = datetime.now(timezone.utc).isoformat()

        if from_store_id == to_store_id:
            raise ValueError("Origin and destination stores must be different.")

        # Check origin store has enough stock
        from_inv = database.inventory.find_one({"company_id": company_id, "store_id": from_store_id, "product_id": product_id.strip()})
        available_qty = from_inv.get("quantity_on_hand", 0) if from_inv else 0
        if available_qty < quantity:
            raise ValueError(f"Insufficient stock at origin store. Requested: {quantity}, Available: {available_qty}")

        # Decrement from origin
        database.inventory.update_one(
            {"company_id": company_id, "store_id": from_store_id, "product_id": product_id.strip()},
            {"$inc": {"quantity_on_hand": -quantity}, "$set": {"last_updated": now}}
        )

        # Increment destination store
        to_inv_id = f"{company_id}-{to_store_id}-{product_id.strip()}"
        database.inventory.update_one(
            {"company_id": company_id, "store_id": to_store_id, "product_id": product_id.strip()},
            {
                "$inc": {"quantity_on_hand": quantity},
                "$setOnInsert": {
                    "inventory_id": to_inv_id,
                    "company_id": company_id,
                    "store_id": to_store_id,
                    "product_id": product_id.strip(),
                    "min_threshold": 5,
                    "max_threshold": 100
                },
                "$set": {"last_updated": now}
            },
            upsert=True
        )

        # Traceable inter-store transfer record
        mov_id = f"MOV-{uuid.uuid4().hex[:8].upper()}"
        movement_doc = {
            "movement_id": mov_id,
            "company_id": company_id,
            "from_store_id": from_store_id,
            "to_store_id": to_store_id,
            "product_id": product_id.strip(),
            "quantity": quantity,
            "movement_type": "TRANSFER",
            "reason": reason or "Inter-Store Stock Transfer",
            "performed_by": performed_by,
            "timestamp": now
        }
        database.inventory_movements.insert_one(movement_doc)
        return movement_doc

    @staticmethod
    def list_movements(
        company_id: int,
        store_id: Optional[int] = None,
        product_id: Optional[str] = None,
        limit: int = 50,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        filter_doc: Dict[str, Any] = {"company_id": company_id}

        if store_id is not None and store_id != 0:
            filter_doc["$or"] = [{"from_store_id": int(store_id)}, {"to_store_id": int(store_id)}]

        if product_id:
            filter_doc["product_id"] = product_id.strip()

        stores_map = {s["store_id"]: s["store_name"] for s in database.stores.find({"company_id": company_id})}
        products_map = {p["product_id"]: p.get("product_name", p["product_id"]) for p in database.products.find({"company_id": company_id})}

        cursor = database.inventory_movements.find(filter_doc).sort("timestamp", -1).limit(limit)
        results = []
        for m in cursor:
            results.append({
                "movement_id": m["movement_id"],
                "company_id": m["company_id"],
                "from_store_id": m.get("from_store_id"),
                "from_store_name": stores_map.get(m.get("from_store_id")) if m.get("from_store_id") else None,
                "to_store_id": m.get("to_store_id"),
                "to_store_name": stores_map.get(m.get("to_store_id")) if m.get("to_store_id") else None,
                "product_id": m["product_id"],
                "product_name": products_map.get(m["product_id"], m["product_id"]),
                "quantity": m["quantity"],
                "movement_type": m["movement_type"],
                "reason": m.get("reason", ""),
                "performed_by": m.get("performed_by"),
                "timestamp": m["timestamp"]
            })
        return results

    @staticmethod
    def get_alerts(company_id: int, store_id: Optional[int] = None, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        items = InventoryRepository.list_inventory(company_id=company_id, store_id=store_id, low_stock_only=True, db=database)
        alerts = []
        for it in items:
            severity = "CRITICAL" if it["quantity_on_hand"] == 0 else "WARNING"
            alerts.append({
                "product_id": it["product_id"],
                "product_name": it["product_name"],
                "category": it["category"],
                "store_id": it["store_id"],
                "store_name": it["store_name"],
                "quantity_on_hand": it["quantity_on_hand"],
                "min_threshold": it["min_threshold"],
                "severity": severity
            })
        return sorted(alerts, key=lambda a: (0 if a["severity"] == "CRITICAL" else 1, a["quantity_on_hand"]))
