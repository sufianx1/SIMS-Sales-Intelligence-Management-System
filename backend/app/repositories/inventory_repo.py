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
        """
        Adjusts inventory stock using atomic conditional operations.
        Prevents race conditions, TOCTOU bugs, and negative inventory under concurrency.
        """
        database = db if db is not None else get_db()
        now = datetime.now(timezone.utc).isoformat()
        prod_id = product_id.strip()
        inv_id = f"{company_id}-{store_id}-{prod_id}"

        if quantity_change < 0:
            reduction = abs(quantity_change)
            # Atomic conditional decrement: Only decrement if quantity_on_hand >= reduction
            result = database.inventory.update_one(
                {
                    "company_id": company_id,
                    "store_id": store_id,
                    "product_id": prod_id,
                    "quantity_on_hand": {"$gte": reduction}
                },
                {
                    "$inc": {"quantity_on_hand": quantity_change},
                    "$set": {"last_updated": now}
                }
            )
            if result.modified_count == 0:
                inv = database.inventory.find_one({"company_id": company_id, "store_id": store_id, "product_id": prod_id})
                available = inv.get("quantity_on_hand", 0) if inv else 0
                raise ValueError(
                    f"Cannot adjust inventory below zero. Current stock is {available}, requested reduction is {reduction}."
                )
        else:
            # Atomic increment / upsert
            database.inventory.update_one(
                {"company_id": company_id, "store_id": store_id, "product_id": prod_id},
                {
                    "$inc": {"quantity_on_hand": quantity_change},
                    "$setOnInsert": {
                        "inventory_id": inv_id,
                        "company_id": company_id,
                        "store_id": store_id,
                        "product_id": prod_id,
                        "min_threshold": 5,
                        "max_threshold": 100
                    },
                    "$set": {"last_updated": now}
                },
                upsert=True
            )

        # Retrieve updated document
        updated_doc = database.inventory.find_one({"company_id": company_id, "store_id": store_id, "product_id": prod_id})

        # Record immutable audit movement
        mov_id = f"MOV-{uuid.uuid4().hex[:8].upper()}"
        movement_doc = {
            "movement_id": mov_id,
            "company_id": company_id,
            "from_store_id": store_id if quantity_change < 0 else None,
            "to_store_id": store_id if quantity_change > 0 else None,
            "product_id": prod_id,
            "quantity": quantity_change,
            "movement_type": "ADJUSTMENT",
            "reason": reason,
            "performed_by": performed_by,
            "timestamp": now
        }
        database.inventory_movements.insert_one(movement_doc)
        return updated_doc or {
            "inventory_id": inv_id,
            "company_id": company_id,
            "store_id": store_id,
            "product_id": prod_id,
            "quantity_on_hand": updated_doc.get("quantity_on_hand", 0) if updated_doc else 0,
            "last_updated": now
        }

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
        """
        Receives stock from supplier, updates inventory with atomic conditional upsert,
        recomputes weighted average cost if cost provided, and records immutable movement log.
        """
        if quantity <= 0:
            raise ValueError("Received quantity must be greater than zero.")

        database = db if db is not None else get_db()
        now = datetime.now(timezone.utc).isoformat()
        prod_id = product_id.strip()
        inv_id = f"{company_id}-{store_id}-{prod_id}"

        # Fetch current product to compute weighted-average cost
        prod = database.products.find_one({"company_id": company_id, "product_id": prod_id})
        current_inv = database.inventory.find_one({"company_id": company_id, "store_id": store_id, "product_id": prod_id})
        current_qty = current_inv.get("quantity_on_hand", 0) if current_inv else 0

        # Weighted Average Cost Policy
        if unit_cost is not None and unit_cost > 0 and prod:
            old_cost = float(prod.get("unit_cost", 0.0))
            if current_qty > 0 and old_cost > 0:
                weighted_cost = round(((current_qty * old_cost) + (quantity * float(unit_cost))) / (current_qty + quantity), 2)
            else:
                weighted_cost = round(float(unit_cost), 2)

            database.products.update_one(
                {"company_id": company_id, "product_id": prod_id},
                {"$set": {"unit_cost": weighted_cost, "last_updated": now}}
            )

        # Atomic increment
        database.inventory.update_one(
            {"company_id": company_id, "store_id": store_id, "product_id": prod_id},
            {
                "$inc": {"quantity_on_hand": quantity},
                "$setOnInsert": {
                    "inventory_id": inv_id,
                    "company_id": company_id,
                    "store_id": store_id,
                    "product_id": prod_id,
                    "min_threshold": 5,
                    "max_threshold": 100
                },
                "$set": {"last_updated": now}
            },
            upsert=True
        )

        updated_doc = database.inventory.find_one({"company_id": company_id, "store_id": store_id, "product_id": prod_id})

        # Record immutable receipt movement
        mov_id = f"MOV-{uuid.uuid4().hex[:8].upper()}"
        movement_doc = {
            "movement_id": mov_id,
            "company_id": company_id,
            "from_store_id": None,
            "to_store_id": store_id,
            "product_id": prod_id,
            "quantity": quantity,
            "movement_type": "RECEIPT",
            "reason": f"Supplier Receipt: {supplier or 'Standard PO'} - {reason or ''}".strip(" -"),
            "performed_by": performed_by,
            "timestamp": now
        }
        database.inventory_movements.insert_one(movement_doc)
        return updated_doc

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
        """
        Performs an inter-store transfer with atomic conditional deduction and compensating rollback.
        Ensures stock cannot be oversold concurrently and maintains transactional consistency.
        """
        if quantity <= 0:
            raise ValueError("Transfer quantity must be greater than zero.")

        if from_store_id == to_store_id:
            raise ValueError("Origin and destination stores must be different.")

        database = db if db is not None else get_db()
        now = datetime.now(timezone.utc).isoformat()
        prod_id = product_id.strip()

        # Step 1: Atomic conditional deduction from origin
        deduct_res = database.inventory.update_one(
            {
                "company_id": company_id,
                "store_id": from_store_id,
                "product_id": prod_id,
                "quantity_on_hand": {"$gte": quantity}
            },
            {
                "$inc": {"quantity_on_hand": -quantity},
                "$set": {"last_updated": now}
            }
        )

        if deduct_res.modified_count == 0:
            from_inv = database.inventory.find_one({"company_id": company_id, "store_id": from_store_id, "product_id": prod_id})
            available_qty = from_inv.get("quantity_on_hand", 0) if from_inv else 0
            raise ValueError(f"Insufficient stock at origin store. Requested: {quantity}, Available: {available_qty}")

        # Step 2: Increment destination store with compensating rollback protection
        to_inv_id = f"{company_id}-{to_store_id}-{prod_id}"
        try:
            database.inventory.update_one(
                {"company_id": company_id, "store_id": to_store_id, "product_id": prod_id},
                {
                    "$inc": {"quantity_on_hand": quantity},
                    "$setOnInsert": {
                        "inventory_id": to_inv_id,
                        "company_id": company_id,
                        "store_id": to_store_id,
                        "product_id": prod_id,
                        "min_threshold": 5,
                        "max_threshold": 100
                    },
                    "$set": {"last_updated": now}
                },
                upsert=True
            )
        except Exception as dest_exc:
            # Compensate: rollback origin deduction to preserve inventory integrity
            database.inventory.update_one(
                {"company_id": company_id, "store_id": from_store_id, "product_id": prod_id},
                {"$inc": {"quantity_on_hand": quantity}, "$set": {"last_updated": now}}
            )
            raise RuntimeError(f"Inter-store transfer failed during destination update. Origin stock was restored: {dest_exc}")

        # Step 3: Record immutable transfer movement
        mov_id = f"MOV-{uuid.uuid4().hex[:8].upper()}"
        movement_doc = {
            "movement_id": mov_id,
            "company_id": company_id,
            "from_store_id": from_store_id,
            "to_store_id": to_store_id,
            "product_id": prod_id,
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
            status = "OUT_OF_STOCK" if it["quantity_on_hand"] == 0 else "LOW_STOCK"
            alerts.append({
                "product_id": it["product_id"],
                "product_name": it["product_name"],
                "category": it["category"],
                "store_id": it["store_id"],
                "store_name": it["store_name"],
                "quantity_on_hand": it["quantity_on_hand"],
                "min_threshold": it["min_threshold"],
                "severity": severity,
                "status": status
            })
        return sorted(alerts, key=lambda a: (0 if a["severity"] == "CRITICAL" else 1, a["quantity_on_hand"]))

    @staticmethod
    def get_rebalance_recommendations(
        company_id: int,
        store_id: Optional[int] = None,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates explainable, deterministic inter-store inventory rebalancing recommendations.
        Identifies branches with stock deficits below minimum threshold alongside branches
        in the same company holding safe surplus beyond their own safety threshold.
        Enforces that donor stores never violate their own minimum safety constraints.
        """
        database = db if db is not None else get_db()
        stores = list(database.stores.find({"company_id": company_id}))
        if len(stores) < 2:
            return []

        stores_map = {s["store_id"]: s.get("store_name", f"Store #{s['store_id']}") for s in stores}
        products_map = {p["product_id"]: p for p in database.products.find({"company_id": company_id})}

        # Query all inventory items for company
        all_inv = list(database.inventory.find({"company_id": company_id}))

        # Group inventory by product_id
        inv_by_product: Dict[str, List[Dict[str, Any]]] = {}
        for item in all_inv:
            pid = item["product_id"]
            inv_by_product.setdefault(pid, []).append(item)

        recommendations = []

        for pid, store_items in inv_by_product.items():
            if len(store_items) < 2:
                continue

            prod = products_map.get(pid, {})
            pname = prod.get("product_name", pid)
            sku = prod.get("sku", pid)
            category = prod.get("category", "General")

            # Identify deficit stores (on hand <= min_threshold or on hand == 0)
            deficits = []
            surpluses = []

            for it in store_items:
                qty = int(it.get("quantity_on_hand", 0))
                min_thresh = int(it.get("min_threshold", 5))
                sid = int(it["store_id"])

                if qty < min_thresh or qty == 0:
                    deficit_qty = max(1, min_thresh - qty)
                    deficits.append({
                        "store_id": sid,
                        "store_name": stores_map.get(sid, f"Store #{sid}"),
                        "current_qty": qty,
                        "min_threshold": min_thresh,
                        "deficit_qty": deficit_qty
                    })
                elif qty > min_thresh:
                    available_surplus = qty - min_thresh
                    surpluses.append({
                        "store_id": sid,
                        "store_name": stores_map.get(sid, f"Store #{sid}"),
                        "current_qty": qty,
                        "min_threshold": min_thresh,
                        "available_surplus": available_surplus
                    })

            if not deficits or not surpluses:
                continue

            # Sort deficits by severity (lowest stock relative to min threshold first)
            deficits.sort(key=lambda d: d["current_qty"])
            # Sort surpluses by highest available surplus first
            surpluses.sort(key=lambda s: s["available_surplus"], reverse=True)

            for d in deficits:
                for s in surpluses:
                    if s["store_id"] == d["store_id"]:
                        continue
                    if s["available_surplus"] <= 0:
                        continue

                    needed = d["deficit_qty"]
                    transfer_qty = min(needed, s["available_surplus"])

                    if transfer_qty <= 0:
                        continue

                    # Filter by store_id if requested
                    if store_id is not None and store_id != 0:
                        if d["store_id"] != int(store_id) and s["store_id"] != int(store_id):
                            continue

                    proj_to = d["current_qty"] + transfer_qty
                    proj_from = s["current_qty"] - transfer_qty

                    urgency = "Critical Out-of-Stock" if d["current_qty"] == 0 else "Low Stock Shortage"
                    summary = f"Rebalance {transfer_qty} units of '{pname}' from {s['store_name']} to {d['store_name']}"

                    explanation = (
                        f"{d['store_name']} has an active {urgency.lower()} with only {d['current_qty']} unit(s) "
                        f"on hand against a safety threshold of {d['min_threshold']}. "
                        f"Meanwhile, {s['store_name']} maintains {s['current_qty']} units (surplus of {s['available_surplus']} "
                        f"above its safety threshold of {s['min_threshold']})."
                    )

                    why_it_matters = (
                        f"Eliminates retail stockout risk and order cancellation at {d['store_name']} without "
                        f"compromising inventory safety at {s['store_name']} or incurring expedited supplier lead-time costs."
                    )

                    rec_action = (
                        f"Initiate an inter-store transfer of {transfer_qty} units from {s['store_name']} "
                        f"to {d['store_name']}."
                    )

                    calc = (
                        f"Recipient Deficit = {d['min_threshold']} (min) - {d['current_qty']} (on hand) = {needed} needed. "
                        f"Donor Safe Surplus = {s['current_qty']} (on hand) - {s['min_threshold']} (min) = {s['available_surplus']} transferable. "
                        f"Transfer Quantity = min({needed}, {s['available_surplus']}) = {transfer_qty} units. "
                        f"Projected Status: {d['store_name']} reaches {proj_to} units; {s['store_name']} safely retains {proj_from} units."
                    )

                    rec_id = f"REC-{company_id}-{s['store_id']}-{d['store_id']}-{pid}"

                    recommendations.append({
                        "recommendation_id": rec_id,
                        "company_id": company_id,
                        "product_id": pid,
                        "product_name": pname,
                        "sku": sku,
                        "category": category,
                        "to_store_id": d["store_id"],
                        "to_store_name": d["store_name"],
                        "to_current_qty": d["current_qty"],
                        "to_min_threshold": d["min_threshold"],
                        "deficit_qty": d["deficit_qty"],
                        "from_store_id": s["store_id"],
                        "from_store_name": s["store_name"],
                        "from_current_qty": s["current_qty"],
                        "from_min_threshold": s["min_threshold"],
                        "available_surplus_qty": s["available_surplus"],
                        "recommended_transfer_qty": transfer_qty,
                        "projected_to_qty": proj_to,
                        "projected_from_qty": proj_from,
                        "summary": summary,
                        "explanation": explanation,
                        "why_it_matters": why_it_matters,
                        "recommended_action": rec_action,
                        "supporting_calculation": calc,
                        "limitations": "Evaluates on-hand recorded stock. Does not account for in-transit shipments or pending layaway orders.",
                        "status": "PROPOSAL"
                    })

                    s["available_surplus"] -= transfer_qty
                    break

        return recommendations
