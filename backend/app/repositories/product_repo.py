"""
app/repositories/product_repo.py
--------------------------------
MongoDB repository for Product catalog operations, strictly scoped to CompanyID.
"""

from typing import Optional, List, Dict, Any, Tuple
from pymongo.database import Database
from app.db.mongo import get_db


class ProductRepository:

    @staticmethod
    def list(
        company_id: int,
        search: Optional[str] = None,
        category: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        db: Optional[Database] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        database = db if db is not None else get_db()
        filter_doc: Dict[str, Any] = {"company_id": company_id}

        if search:
            regex = {"$regex": search.strip(), "$options": "i"}
            filter_doc["$or"] = [{"product_name": regex}, {"product_id": regex}, {"sku": regex}]

        if category and category != "All":
            filter_doc["category"] = category.strip()

        total = database.products.count_documents(filter_doc)
        cursor = database.products.find(filter_doc).skip(offset).limit(limit)

        items = []
        for p in cursor:
            # Aggregate sales for this product across orders
            pipeline = [
                {"$match": {"company_id": company_id, "lines.product_id": p["product_id"]}},
                {"$unwind": "$lines"},
                {"$match": {"lines.product_id": p["product_id"]}},
                {"$group": {
                    "_id": None,
                    "total_sales": {"$sum": "$lines.sales"},
                    "total_quantity": {"$sum": "$lines.quantity"},
                    "total_profit": {"$sum": "$lines.profit"}
                }}
            ]
            agg = list(database.orders.aggregate(pipeline))
            stats = agg[0] if agg else {"total_sales": 0.0, "total_quantity": 0, "total_profit": 0.0}

            items.append({
                "product_id": p["product_id"],
                "product_name": p["product_name"],
                "category": p.get("category", "General"),
                "sub_category": p.get("sub_category", ""),
                "sku": p.get("sku", p["product_id"]),
                "unit_cost": float(p.get("unit_cost", 0.0)),
                "unit_price": float(p.get("unit_price", 0.0)),
                "company_id": p["company_id"],
                "total_sales": round(float(stats["total_sales"]), 2),
                "total_quantity": int(stats["total_quantity"]),
                "total_profit": round(float(stats["total_profit"]), 2)
            })

        return items, total

    @staticmethod
    def get_by_id(company_id: int, product_id: str, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        database = db if db is not None else get_db()
        p = database.products.find_one({"company_id": company_id, "product_id": product_id.strip()})
        if not p:
            return None

        pipeline = [
            {"$match": {"company_id": company_id, "lines.product_id": product_id.strip()}},
            {"$unwind": "$lines"},
            {"$match": {"lines.product_id": product_id.strip()}},
            {"$group": {
                "_id": None,
                "total_sales": {"$sum": "$lines.sales"},
                "total_quantity": {"$sum": "$lines.quantity"},
                "total_profit": {"$sum": "$lines.profit"}
            }}
        ]
        agg = list(database.orders.aggregate(pipeline))
        stats = agg[0] if agg else {"total_sales": 0.0, "total_quantity": 0, "total_profit": 0.0}

        return {
            "product_id": p["product_id"],
            "product_name": p["product_name"],
            "category": p.get("category", "General"),
            "sub_category": p.get("sub_category", ""),
            "sku": p.get("sku", p["product_id"]),
            "unit_cost": float(p.get("unit_cost", 0.0)),
            "unit_price": float(p.get("unit_price", 0.0)),
            "company_id": p["company_id"],
            "total_sales": round(float(stats["total_sales"]), 2),
            "total_quantity": int(stats["total_quantity"]),
            "total_profit": round(float(stats["total_profit"]), 2)
        }

    @staticmethod
    def get_order_history(company_id: int, product_id: str, limit: int = 50, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        cursor = database.orders.find(
            {"company_id": company_id, "lines.product_id": product_id.strip()}
        ).sort("order_date", -1).limit(limit)

        results = []
        for o in cursor:
            # Look up customer name
            cust = database.customers.find_one({"company_id": company_id, "customer_id": o["customer_id"]})
            cust_name = cust["customer_name"] if cust else o.get("customer_id", "")
            for line in o.get("lines", []):
                if line.get("product_id") == product_id.strip():
                    results.append({
                        "order_id": o["order_id"],
                        "order_date": o.get("order_date", ""),
                        "customer_name": cust_name,
                        "sales": round(float(line.get("sales", 0.0)), 2),
                        "quantity": int(line.get("quantity", 1)),
                        "discount": round(float(line.get("discount", 0.0)), 2),
                        "profit": round(float(line.get("profit", 0.0)), 2)
                    })
        return results

    @staticmethod
    def create(company_id: int, product_id: str, product_name: str, category: Optional[str], sub_category: Optional[str], sku: Optional[str] = None, unit_cost: float = 0.0, unit_price: float = 0.0, db: Optional[Database] = None):
        database = db if db is not None else get_db()
        clean_sku = (sku or product_id).strip()
        doc = {
            "product_id": product_id.strip(),
            "product_name": product_name.strip(),
            "category": category or "General",
            "sub_category": sub_category or "",
            "sku": clean_sku,
            "unit_cost": float(unit_cost),
            "unit_price": float(unit_price),
            "company_id": company_id,
            "is_active": True
        }
        database.products.update_one(
            {"company_id": company_id, "product_id": product_id.strip()},
            {"$set": doc},
            upsert=True
        )

    @staticmethod
    def update(company_id: int, product_id: str, product_name: Optional[str] = None, category: Optional[str] = None, sub_category: Optional[str] = None, sku: Optional[str] = None, unit_cost: Optional[float] = None, unit_price: Optional[float] = None, db: Optional[Database] = None):
        database = db if db is not None else get_db()
        updates = {}
        if product_name is not None:
            updates["product_name"] = product_name.strip()
        if category is not None:
            updates["category"] = category.strip()
        if sub_category is not None:
            updates["sub_category"] = sub_category.strip()
        if sku is not None:
            updates["sku"] = sku.strip()
        if unit_cost is not None:
            updates["unit_cost"] = float(unit_cost)
        if unit_price is not None:
            updates["unit_price"] = float(unit_price)

        if updates:
            database.products.update_one(
                {"company_id": company_id, "product_id": product_id.strip()},
                {"$set": updates}
            )
